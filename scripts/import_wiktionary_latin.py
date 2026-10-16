"""Import Latin lemmas from the pinned Wiktionary dump into data/*.csv.

    python3 scripts/import_wiktionary_latin.py [--dry-run] [--limit N]

Reads raw/raw-wiktextract-data.jsonl.gz (see scripts/fetch_wiktextract.py) and
refuses to run unless its sha256 matches the one recorded on the source row.
Language rows (with their parents, up to the top family) come from Wiktionary's
language modules (wiktionary_languages.py).
Loads the current data/ into a database, adds the rows, checks them, and
exports. Refuses to run if rows from this source already exist; to redo an
import, revert it in git first. --limit implies --dry-run.

Scope: Latin lemmas only. A sense is an inflected form of another entry if it
has `form_of` or Wiktionary files it under "... non-lemma forms"; an entry is
skipped when all its senses are, and such senses are left out of the meanings
of entries that are kept. Alternative spellings (`alt_of`) are kept. A few
hundred inflected forms carry neither marker and cannot be told apart without
guessing from the gloss text, so they are imported.
"""
import argparse
import gzip
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db  # noqa: E402
import kaikki  # noqa: E402
import wiktionary_languages as wl  # noqa: E402

DUMP_TARGET = kaikki.TARGETS["dump"]
DUMP = DUMP_TARGET.dest
SOURCE_ID = DUMP_TARGET.source_id
LANG = "la"

# Etymology templates we turn into rows, and the relation text we store.
# For all but `cog`, argument 1 is the language of the word being described,
# so only templates whose argument 1 is Latin describe the entry itself.
RELATIONS = {
    "inh": "inherited", "inh+": "inherited",
    "bor": "borrowed", "bor+": "borrowed",
    "lbor": "learned borrowing", "slbor": "semi-learned borrowing",
    "der": "derived", "der+": "derived",
    "calque": "calque", "cal": "calque", "clq": "calque",
    "sl": "semantic loan", "translit": "transliteration",
    "doublet": "doublet",
    "cog": "cognate",
}


def stream(pattern):
    """Yield parsed top-level entries whose line contains `pattern` (a regex)."""
    rx = re.compile(pattern)
    with gzip.open(DUMP, "rt", encoding="utf-8") as f:
        for line in f:
            if rx.search(line):
                yield json.loads(line)


def is_inflection(sense):
    """An inflected form of another entry, by `form_of` or Wiktionary's own category."""
    return "form_of" in sense or any(
        "non-lemma" in c.lower() for c in sense.get("categories", []))


def is_inflected_form(entry):
    senses = entry.get("senses", [])
    return bool(senses) and all(is_inflection(s) for s in senses)


def oneline(s):
    """Collapse all whitespace, so no cell has a line break."""
    return re.sub(r"\s+", " ", s).strip() if s else s


def strip_marks(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def headword(entry):
    """The form with diacritics when Wiktionary gives one, else the page title."""
    word = entry["word"]
    for f in entry.get("forms", []):
        if "canonical" in f.get("tags", []) and strip_marks(f["form"]) == word:
            return f["form"]
    return word


def page_ref(word):
    return f"https://en.wiktionary.org/wiki/{quote(word.replace(' ', '_'))}#Latin"


def slug(word):
    return re.sub(r"\s+", "_", word)


def clean_form(s):
    s = oneline(re.sub(r"<[^>]*>", "", s or ""))
    return None if s in ("", "-") else s


def etymology_rows(entry, skipped):
    """Yield (relation, language_code, form, notes) for one entry."""
    seen = set()
    for t in entry.get("etymology_templates", []):
        name, args = t["name"], t.get("args", {})
        if name not in RELATIONS:
            skipped[name] += 1
            continue
        if name == "cog":
            codes, form = args.get("1", "").split(","), clean_form(args.get("2"))
            gloss = args.get("t") or args.get("gloss") or args.get("4")
        else:
            if args.get("1") != LANG:
                skipped[name + " (not about this entry)"] += 1
                continue
            codes = args.get("2", "").split(",") if name != "doublet" else [LANG]
            form = clean_form(args.get("3" if name != "doublet" else "2"))
            gloss = args.get("t") or args.get("gloss") or args.get("5")
        notes = oneline("; ".join(x for x in (
            f"gloss: {gloss}" if gloss else None,
            f"transliteration: {args['tr']}" if args.get("tr") else None) if x))
        for code in (c.strip() for c in codes):
            key = (name, code, form)
            if code and key not in seen:
                seen.add(key)
                yield RELATIONS[name], code, form, notes


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    ap.add_argument("--limit", type=int, help="stop after N Latin entries (implies --dry-run)")
    args = ap.parse_args()
    dry = args.dry_run or args.limit is not None

    print(f"checking {DUMP.name} against the source row ...", file=sys.stderr)
    kaikki.verify(DUMP_TARGET)
    langs = wl.load()

    con = db.connect(":memory:")
    db.load(con)
    if con.execute("SELECT 1 FROM lexeme WHERE source_id=?", (SOURCE_ID,)).fetchone():
        raise SystemExit("rows from this source already exist; revert them in git to redo")

    lexemes, prons, means, etys = [], [], [], []
    used_codes = {LANG}
    counter = Counter()
    skipped = Counter()
    stats = Counter()
    n_seen = 0

    for e in stream(r'"lang_code": "la"'):
        if e.get("lang_code") != LANG:
            continue
        n_seen += 1
        if args.limit and n_seen > args.limit:
            break
        if is_inflected_form(e):
            stats["skipped inflected forms"] += 1
            continue
        word = e["word"]
        counter[slug(word)] += 1
        suffix = f"{LANG}-{slug(word)}-{counter[slug(word)]}"
        lid = f"lex-{suffix}"
        ref = page_ref(word)
        lexemes.append((lid, langs.id(LANG), oneline(headword(e)), e.get("pos"), None,
                        "extracted", SOURCE_ID, ref, None))

        seen = set()
        for s in e.get("sounds", []):
            if "ipa" not in s:
                continue
            variety = oneline(", ".join(s["tags"]) if s.get("tags") else s.get("note"))
            ipa = oneline(s["ipa"])
            if (ipa, variety) not in seen:
                seen.add((ipa, variety))
                prons.append((f"pron-{suffix}-{len(seen)}", lid, ipa, variety,
                              SOURCE_ID, ref))

        k = 0
        for s in e.get("senses", []):
            if is_inflection(s) or not s.get("glosses"):
                continue
            k += 1
            means.append((f"mean-{suffix}-{k}", lid, oneline("; ".join(s["glosses"])), None,
                          "attested", SOURCE_ID, ref))

        k = 0
        for relation, code, form, notes in etymology_rows(e, skipped):
            k += 1
            used_codes.add(code)
            etys.append((f"ety-{suffix}-{k}", lid, relation, None, langs.id(code),
                         form, SOURCE_ID, ref, notes or None))

    print(f"{len(lexemes)} lexemes, {len(prons)} pronunciations, {len(means)} meanings, "
          f"{len(etys)} etymologies, {len(used_codes)} languages; {dict(stats)}")
    print("etymology templates not imported:", dict(skipped.most_common(15)))
    if dry:
        print("dry run: nothing written")
        return 0

    con.executemany("INSERT OR IGNORE INTO language VALUES (?,?,?,?,?,?)", langs.rows(used_codes))
    con.executemany("INSERT INTO lexeme VALUES (?,?,?,?,?,?,?,?,?)", lexemes)
    con.executemany("INSERT INTO pronunciation VALUES (?,?,?,?,?,?)", prons)
    con.executemany("INSERT INTO meaning VALUES (?,?,?,?,?,?,?)", means)
    con.executemany("INSERT INTO etymology VALUES (?,?,?,?,?,?,?,?,?)", etys)
    con.commit()
    problems = db.check(con)
    if problems:
        print("\n".join(problems[:20]))
        return 1
    db.export(con)
    print("exported to data/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
