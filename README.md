# Ancient Lexicon Database (working title)

An open, openly licensed database of words from ancient languages: their forms,
pronunciations, meanings, and etymologies, each recorded with its source.

The first goal is to support work on **Linear A**, the undeciphered Minoan
script, by collecting in one place the Linear A inscriptions and the vocabulary
of languages that were spoken near it in time and place (for example Greek,
Mycenaean, Phoenician and other Semitic languages, Egyptian, and the Anatolian
languages). The scope is meant to grow over time to more languages, so the
database is not specific to Linear A.

> **Status: design stage.** The schema and conventions below are decided in
> outline. The data files, scripts and exports described here do not exist yet.

## What this project is, and is not

This repository holds **data and attributed claims**: what the inscriptions say,
what words exist, and what scholars have proposed about them.

It does **not** hold research or analysis. Anything that interprets the data
(look-alike matching, statistics, embeddings, morphology) belongs in separate
projects that read from this one. Keeping them apart means that nothing in the
database is an unvalidated guess presented as a finding, and that anyone can use
the data for their own analysis.

Two rules follow from this:

- **Every claim has a source.** Pronunciations, meanings and etymologies are
  never stated as bare facts. Each one records who said it and where.
- **Disagreement is data.** Competing meanings or etymologies for one word are
  stored side by side as separate rows. Nothing is overwritten to settle a
  dispute.

## How the data is stored

The canonical data is a set of **CSV files in this git repository**, one per
table. Git history is the audit trail: it shows what changed, when, and who
changed it.

To make changes, the CSVs are loaded into a temporary SQL database, edited with
scripts and queries, and exported back to CSV. The database is disposable. The
CSVs in git are the only source of truth.

```
CSV files (git)  --load-->  temporary SQL database  --export-->  CSV files (git)
      ^                       (importers, merges,                       |
      |                        constraint checks)                       v
      +----------------------- pull request <---------------------------+
```

The database engine for the working copy is not yet chosen (SQLite, DuckDB and
PostgreSQL are all candidates). Nothing in the data depends on it.

## Browsing the data

To look through the tables in a web browser (search, filter, follow references
between tables, run read-only SQL), use [Datasette](https://datasette.io):

```
pip install -r requirements.txt
python3 scripts/browse.py          # serves http://127.0.0.1:8001
```

This rebuilds the disposable `work.db` from `data/*.csv` and serves it
read-only. Edit the CSVs, then restart to see changes.

The latest release is also hosted at
<https://alexjfdev.github.io/language-project/>, rebuilt automatically
whenever `release` changes. It runs Datasette in your browser
([Datasette Lite](https://github.com/simonw/datasette-lite)), so the first
load downloads the whole database and is slow.

## Planned repository layout

```
data/        one CSV file per table (the canonical data)
schema/      the schema and a description of every table and column
scripts/     load, export, validation, and one importer per source
raw/         downloaded source material (git-ignored, not published)
docs/        source registry, conventions, how to contribute
```

## The data model

Every table has an `id`. Columns ending in `_id` refer to a row in another table.

**Provenance**
- `source`: a book, article, database or dictionary, with its citation, link,
  and license.
- `contributor`: a person who adds data.

**Reference**
- `language`: a language we hold words from. Includes a "Linear A (unknown)"
  entry. `parent_id` points to the immediate parent: the family a language
  belongs to, or the language an older variety is a stage of (Old Latin points
  to Latin). Families are rows too and point to larger families. A language's
  family is found by following parents, not stored on it, since families are
  more disputed than immediate ancestry.
- `script`: a writing system.
- `semantic_field`: a meaning category such as cloth, grain or metal.

**Script evidence**
- `sign`: one character of a script.
- `sign_value`: a proposed sound for a sign. Kept separate because these sounds
  are certain for Linear B but only assumed for Linear A.
- `word_form`, `word_form_sign`: a distinct sequence of signs, independent of
  meaning, and its ordered signs.
- `inscription`: a physical object such as a tablet.
- `token`, `token_sign`: one item on a line of an inscription (a word, an
  ideogram, a number), and the signs of that specific occurrence, with how
  certain each reading is.

**Words and claims about them**
- `lexeme`: a word in any language, including Linear A words.
- `pronunciation`: a pronunciation of a word, in IPA. A word can have several.
- `meaning`: a meaning of a word. A word can have several, each with a status
  (attested, proposed, disputed, rejected).
- `etymology`: a claim about where a word came from (inherited, borrowed,
  cognate), naming the proposed source word or language.

A word's pronunciations, meanings and etymologies each point to the word and to
the source that made the claim.

## Conventions

These keep the CSV files readable in git and the data traceable.

- **Stable text IDs.** Every row gets a readable ID when it is first created
  (for example `src-damos-2024`) and keeps it forever. IDs are never reused or
  renumbered, because rows refer to each other by ID.
- **Deterministic export.** Rows are sorted by ID, columns are in a fixed order,
  files are UTF-8 with consistent line endings. Loading the CSVs and exporting
  them again with no changes must produce no diff.
- **One row per line.** No multi-line text in cells.
- **Facts, not prose.** Record the word, form, and a short gloss, with a
  citation. Glosses may be taken from a source as written, under that source's
  license (recorded on its `source` row). Do not copy example sentences or
  etymology write-ups.
- **Record where in the source.** Claims should say where to find them: a page
  number, entry, or URL.
- **Record how a row was obtained.** Each lexeme notes whether it was copied
  from a source, extracted as a plain fact, independently derived, or written
  by a contributor.
- **Record the license.** Every source carries its license, and every row
  points to its source, so an openly licensed subset can be published and
  restricted material left out.
- **Avoid spreadsheet programs for editing.** Excel can silently change
  encodings and reformat cells, which corrupts the Linear A and Linear B signs.
  Use a plain-text editor, or load the data into the working database.

## Adding a new source

1. **Register it** in `docs/` with its URL, license, whether its terms allow
   scraping or bulk reuse, and how to obtain it (dump, API, or page).
   Do not scrape a source whose terms forbid it. Prefer bulk downloads and APIs
   over scraping pages, and fetch slowly.
2. **Download the raw material** into `raw/`. This folder is git-ignored and is
   never published, because a downloaded page can be copyrighted even when the
   facts in it are not.
3. **Write an importer** in `scripts/` that extracts facts (not copied text) into
   proposed rows.
4. **Merge, do not duplicate.** If the word already exists (same language and
   form), attach the new claims to the existing word, each with its own source.
   Ambiguous matches go to a review file instead of being guessed.
5. **Stage and verify any LLM-extracted data.** Output from a model reading a
   book is written to a staging file, checked by a person against the book, and
   only then merged. Models misread and invent entries.
6. **Review the diff and commit** one import per commit, with the source named in
   the message. A bad import can then be undone with a single `git revert`.

## Roles

- **Finding sources and judging the linguistics** (which sources to use, how
  entries correspond across sources, what a reading means): the linguist.
- **Compiling the data** (importers, merging, validation, tooling): the
  engineer.

## License

The code (`scripts/`, `schema/`) is under the [MIT License](LICENSE).

The data (`data/`) is licensed per row, by source. Original contributions are
[CC0](https://creativecommons.org/publicdomain/zero/1.0/). Material derived
from Wiktionary is [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/),
because it is share-alike. Other sources keep their own terms. Each row points
to its source and each source records its license, so you can take only the
rows you can use. See [LICENSE-DATA.md](LICENSE-DATA.md) for details.

## Citing

Tagged releases will be archived (for example on Zenodo) so that each version
has a permanent identifier. Cite the release you used.