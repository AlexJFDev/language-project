"""Wiktionary language codes -> `language` rows, for any importer that reads Wiktionary.

Wiktionary names its languages in Lua data modules, not in the entry dump, so
etymology-only languages (Old Latin, Biblical Hebrew), families (Celtic) and
reconstructed languages (Proto-Indo-European) have no entries to read a name
from. This reads the modules archive from kaikki.org instead.

In an importer:

    import wiktionary_languages as wl
    langs = wl.load()                  # exits unless the archive matches its source row
    langs.id("VL.")                    # "lang-la-vul": id to put in foreign keys
    rows = langs.rows(codes)           # `language` rows for codes and all their ancestors

Rows are (id, name, iso_code, parent_id, period, notes). `parent_id` is the
immediate parent Wiktionary lists: a family for a language, a language for an
etymology-only variety (Old Latin -> Latin), a larger family for a family. The
chain up to the top is included, so every parent_id points at a row. A family is
therefore found by walking parents, not stored on the language. A language with
no known family (Wiktionary's "not a family" placeholder) has no parent.

Ids are `lang-<code>`, or `lang-fam-<code>` for families: three codes (gn, ku,
kv) are both a language and a family. Codes are canonical: old codes Wiktionary
still accepts (`VL.` for `la-vul`) are aliases and resolve to the same row.
A row's notes start with "Wiktionary language code: <code>".

    python3 scripts/wiktionary_languages.py lookup CODE...

Standard library only.
"""
import re
import sys
import tarfile
from dataclasses import dataclass

import kaikki

TARGET = kaikki.TARGETS["modules"]
NOTES_PREFIX = "Wiktionary language code: "

# Members to read, in priority order: a code found in an earlier one wins.
FILES = [
    ("language", re.compile(r"Module/languages/data/(2|3/[a-z]|exceptional)\.txt$")),
    ("etymology-only", re.compile(r"Module/etymology languages/data\.txt$")),
    ("language", re.compile(r"Module/wikimedia languages/data\.txt$")),
    ("family", re.compile(r"Module/families/data\.txt$")),
]

# export.aliases = { ["VL."] = "la-vul", ... } in Module/languages/data
ALIASES_FILE = re.compile(r"Module/languages/data\.txt$")
ALIASES_BLOCK = re.compile(r"export\.aliases\s*=\s*\{(.*?)\n\}", re.DOTALL)
ALIAS = re.compile(r'\["([^"]+)"\]\s*=\s*"([^"]+)"')

# m["code"] = { "Name", <wikidata id>, "<family or parent code>", ...
# Comments may sit between the brace and the name.
ENTRY = re.compile(
    r'^m\["((?:[^"\\]|\\.)+)"\]\s*=\s*\{\s*(?:--[^\n]*\n\s*)*"((?:[^"\\]|\\.)*)"',
    re.MULTILINE)
# Wiktionary's placeholder for "no family" (isolates, unclassified languages). It
# lists itself as its parent, so it is not a parent here: those rows get none.
NO_PARENT = {"qfa-not"}
PARENT = re.compile(r'\s*,\s*(?:nil|\d+)\s*,\s*"([^"]+)"')


@dataclass(frozen=True)
class Entry:
    code: str            # the canonical code
    name: str
    kind: str            # language, reconstructed, etymology-only or family
    parent: str | None   # parent code: a family, or for etymology-only a language

    @property
    def id(self):
        return f"lang-fam-{self.code}" if self.kind == "family" else f"lang-{self.code}"


def unescape(s):
    return s.replace('\\"', '"').replace("\\\\", "\\")


def parse(text, kind):
    matches = list(ENTRY.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end]
        parent = PARENT.match(body)
        entry_kind = ("reconstructed" if kind == "language"
                      and re.search(r'type\s*=\s*"reconstructed"', body) else kind)
        yield Entry(unescape(m.group(1)), unescape(m.group(2)), entry_kind,
                    parent.group(1) if parent else None)


class Languages:
    def __init__(self, languages, families, aliases):
        self.languages = languages   # includes reconstructed and etymology-only
        self.families = families
        self.aliases = aliases

    def get(self, code):
        """The entry for a code as written in a template: a language if there is one
        (aliases resolved), else a family; None if Wiktionary does not define it."""
        code = self.aliases.get(code, code)
        return self.languages.get(code) or self.families.get(code)

    def id(self, code):
        e = self.get(code)
        return e.id if e else f"lang-{code}"

    def parent(self, entry):
        """The parent entry, looked up in the right namespace, or None."""
        if not entry.parent or entry.parent in NO_PARENT:
            return None
        code = self.aliases.get(entry.parent, entry.parent)
        if entry.kind == "etymology-only":
            return self.languages.get(code) or self.families.get(code)
        return self.families.get(code) or self.languages.get(code)

    def row(self, entry, code=None):
        """A `language` row. Pass `code` with entry=None for an undefined code."""
        if entry is None:
            return (f"lang-{code}", code, None, None, None,
                    f"{NOTES_PREFIX}{code}; name not found in Wiktionary's language data")
        parent = self.parent(entry)
        notes = NOTES_PREFIX + entry.code
        if entry.kind != "language":
            notes += "; " + entry.kind
        return (entry.id, entry.name, None, parent.id if parent else None, None, notes)

    def rows(self, codes):
        """Rows for these codes and all their ancestors, sorted by id."""
        out = {}
        for code in codes:
            e = self.get(code)
            if e is None:
                r = self.row(None, code)
                out[r[0]] = r
                continue
            while e is not None and e.id not in out:
                out[e.id] = self.row(e)
                e = self.parent(e)
        return [out[k] for k in sorted(out)]


def load(path=None, check=True):
    """Read the modules archive. With check (the default), exit unless it is the
    build recorded on its source row."""
    if check:
        kaikki.verify(TARGET)
    path = path or TARGET.dest
    members = {}
    aliases_text = ""
    with tarfile.open(path, "r:gz") as tar:
        for member in tar:
            if not member.isfile():
                continue
            if ALIASES_FILE.search(member.name):
                aliases_text = tar.extractfile(member).read().decode("utf-8")
            for rank, (kind, rx) in enumerate(FILES):
                if rx.search(member.name):
                    members[member.name] = (rank, kind, tar.extractfile(member).read())
    languages, families = {}, {}
    for _, kind, data in sorted(members.values(), key=lambda v: v[0]):
        target = families if kind == "family" else languages
        for e in parse(data.decode("utf-8"), kind):
            target.setdefault(e.code, e)
    block = ALIASES_BLOCK.search(aliases_text)
    aliases = {a: c for a, c in ALIAS.findall(block.group(1) if block else "")
               if c in languages}
    return Languages(languages, families, aliases)


def main(argv):
    if len(argv) >= 3 and argv[1] == "lookup":
        langs = load()
        for code in argv[2:]:
            e = langs.get(code)
            if not e:
                print(f"{code}\tnot found")
                continue
            p = langs.parent(e)
            print(f"{code}\t{e.id}\t{e.name}\t{e.kind}\tparent: {p.id if p else '-'}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
