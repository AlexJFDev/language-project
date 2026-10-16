# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

An open database of words and inscriptions from ancient languages (first goal: Linear A). It holds **data and attributed claims only**. Analysis (look-alike matching, statistics, embeddings, morphology) belongs in separate projects that read from this one. See `README.md` for the full data model and the "Adding a new source" workflow. Latin lemmas from Wiktionary are imported (`docs/sources/wiktionary.md`); the script-evidence tables (signs, inscriptions, tokens) are still empty. Source registry notes live in `docs/sources/`.

## Architecture

The CSVs in `data/` (one per table) are the **only source of truth**. SQLite (`work.db`, git-ignored) is a disposable working copy:

```
data/*.csv --load--> SQLite (schema/schema.sql) --export--> data/*.csv
```

- `schema/schema.sql` defines table order and column order for both load and export. Tables must be declared after the tables they reference; `scripts/db.py` loads and exports in `sqlite_master` rowid order, so declaration order is dependency order.
- A CSV header must exactly match the schema's column order, or load fails. Adding a column means editing the schema and every affected CSV header together.
- Empty CSV cells load as `NULL` and `NULL` exports as empty cells.
- `scripts/db.py` is stdlib-only. `requirements.txt` is for future importers.
- Importers load the current `data/` through `db.py`, add rows, run its check, and export. They must refuse to run if their source's rows already exist. Revert an import in git to redo it.
- Downloaded source files are pinned by sha256 on their `source` row (kaikki.org overwrites its files weekly). `scripts/kaikki.py` has the download and `verify` helpers, and `scripts/wiktionary_languages.py` turns Wiktionary language codes into `language` rows (with ancestors) and ids; reuse them in any Wiktionary importer.

## Commands

```bash
python3 scripts/db.py check       # load into memory, report bad foreign-key references
python3 scripts/db.py load [db]   # rebuild work.db (default ./work.db) from schema + CSVs, then check
python3 scripts/db.py export [db] # write the db back to data/*.csv
python3 scripts/db.py roundtrip   # load then export; fails if data/ changes

python3 scripts/fetch_wiktextract.py [dump|modules]   # download and checksum a kaikki.org file into raw/
python3 scripts/import_wiktionary_latin.py [--dry-run] [--limit N]   # about 10 minutes; verifies the dump first
python3 scripts/wiktionary_languages.py lookup CODE...   # Wiktionary language code to id, name, kind, parent
```

There is no test suite or linter yet. `roundtrip` is the closest thing: it must print `no diff` after any change to `data/` or the schema. It rewrites `data/` in place, so run it on a clean working tree.

## Data conventions that affect code and edits

- IDs are stable readable text (e.g. `src-damos-2024`), never reused or renumbered, because other rows reference them.
- Export is deterministic: rows sorted by `id`, schema column order, UTF-8, LF endings. Loading and exporting with no edits must produce no diff.
- One row per line (no multi-line cells). Do not edit CSVs with spreadsheet programs, since they corrupt encodings and the Linear A/B signs.
- Every claim (pronunciation, meaning, etymology, sign value) must reference a `source` and ideally the location within it. Competing claims are separate rows; never overwrite one to settle a dispute.
- Record facts and short glosses (which may be taken from a source as written, under that source's license), not example sentences or etymology write-ups. Downloaded source material goes in `raw/` (git-ignored, never published).
- LLM-extracted data goes to a staging file for human verification before merging. One import per commit, with the source named in the message.
