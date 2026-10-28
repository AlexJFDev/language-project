"""Import Greek lemmas from the pinned Wiktionary dump into data/*.csv.

    python3 scripts/import_wiktionary_greek.py [--dry-run] [--limit N]

Imports every Greek language that has entries of its own in Wiktionary:
Ancient Greek, Greek (Modern), Mycenaean Greek, Proto-Hellenic, Pontic Greek,
Tsakonian, Cappadocian Greek and Yevanic. Varieties that are only etymology
labels (Koine, Attic, Doric, ...) have no entries and are not imported.

Everything else works as in import_wiktionary_latin.py, which holds the shared
code and describes the scope: lemmas only, inflected forms are skipped, one
pass over raw/raw-wiktextract-data.jsonl.gz, and the import refuses to run if
rows of this source already exist for any of these languages.

Notes on the data:
- Mycenaean Greek entries are headed in Linear B script (the syllable signs,
  logograms and words); Wiktionary gives the romanization in `forms`, which is
  not imported.
- Proto-Hellenic words are reconstructions, so their page_ref is the
  `Reconstruction:Proto-Hellenic/...` page, and their words carry no asterisk
  in the dump.
- Etymology templates of the newer `ety`/`etymon` kind are not imported,
  as with Latin; the count of skipped templates is printed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import import_wiktionary_latin as shared  # noqa: E402

GREEK = {
    "grc": ("Ancient Greek", False),
    "el": ("Greek", False),
    "gmy": ("Mycenaean Greek", False),
    "grk-pro": ("Proto-Hellenic", True),
    "pnt": ("Pontic Greek", False),
    "tsd": ("Tsakonian", False),
    "cpg": ("Cappadocian Greek", False),
    "yej": ("Yevanic", False),
}

if __name__ == "__main__":
    sys.exit(shared.run(GREEK, __doc__))
