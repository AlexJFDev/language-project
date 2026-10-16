# English Wiktionary (via kaikki.org)

Source row: `src-wiktionary-en-20260902` in `data/source.csv`.

| | |
|---|---|
| Content | Words, pronunciations, glosses and etymologies for many languages. Used first for Latin. |
| Where | https://kaikki.org/dictionary/rawdata.html |
| File | `https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz` (all languages, about 3GB) |
| License | CC BY-SA 4.0 (Wiktionary's license). kaikki.org states none itself. Attribution and share-alike apply to the rows taken from it. |
| Bulk reuse | Yes. kaikki.org publishes bulk downloads for this purpose. Do not scrape Wiktionary pages. |
| Cite | Ylonen, Tatu. 2022. Wiktextract: Wiktionary as Machine-Readable Structured Data. Proceedings of the 13th LREC, pp. 1317-1325, Marseille. |

## The pinned build

| | |
|---|---|
| Wiktionary dump | enwiktionary, dated 2026-09-02 |
| Extracted | 2026-10-03 with wiktextract `1a05e46` and wikitextprocessor `e3d6d4e` |
| Size | 2,981,058,381 bytes |
| sha256 | `3dac8a09e57827bef493e2e6b552fe917bf3b1fc55dee05c4e4a3702aff5dbdb` |
| kaikki.org Last-Modified | Sat, 03 Oct 2026 08:24:38 GMT |
| Downloaded | 2026-10-16 |

kaikki.org overwrites this file about weekly and keeps no dated copies. The URL
therefore will not return this build later. The checksum is how to tell: run

    python3 scripts/fetch_wiktextract.py --sha256 3dac8a09e57827bef493e2e6b552fe917bf3b1fc55dee05c4e4a3702aff5dbdb

which exits 1 if kaikki.org now serves a different build. The file is kept in
`raw/` (git-ignored) and is not published. A permanent archive of the Latin
extract is not made yet.

## The pinned modules archive (language names)

Wiktionary names its languages in Lua data modules, not in the entry dump.
Etymology-only languages (Old Latin), families (Celtic) and reconstructed
languages (Proto-Indo-European) have no entries to read a name from, so names
come from this archive.

Source row: `src-wiktionary-modules-20261003` in `data/source.csv`.

| | |
|---|---|
| File | `https://kaikki.org/dictionary/wiktionary-modules.tar.gz` |
| Size | 93,167,262 bytes |
| sha256 | `bb21b9d06d5119eb1d4785fc1b341f57dc5da14d3079573bcaedbf9bbe93fe6e` |
| kaikki.org Last-Modified | Sat, 03 Oct 2026 10:23:58 GMT |
| Downloaded | 2026-10-16 |

kaikki.org gives no build date or version for this archive, only Last-Modified,
and it is overwritten about weekly like the dump. Fetch and verify it with
`python3 scripts/fetch_wiktextract.py modules`.

## Shared code for Wiktionary importers

- `scripts/kaikki.py`: downloads, checksums, and `verify`, which exits unless a
  file in `raw/` matches the checksum on its source row. To use another
  kaikki.org file, add a `Target` there and register its source row.
- `scripts/wiktionary_languages.py`: Wiktionary language code to `language`
  rows. An importer calls `load()` once, `langs.id(code)` for the id to put in
  a foreign key, and `langs.rows(codes)` for the rows to insert. The rows
  include every ancestor, so each `parent_id` points at a row. Ids are
  `lang-<code>`, and `lang-fam-<code>` for families (`gn`, `ku` and `kv` are
  both a language and a family). Old codes Wiktionary still accepts (`VL.`,
  `sa-ved`) are aliases of canonical ones (`la-vul`, `vsn`) and resolve to the
  same row. `parent_id` is the parent Wiktionary lists: the family of a
  language, the language of an etymology-only variety, the larger family of a
  family. Notes say whether a row is a family, reconstructed or etymology-only.
  `python3 scripts/wiktionary_languages.py lookup CODE...` looks codes up by
  hand.

## Notes for importers

- Latin entries have `lang_code` `la`. The scope of the first import is
  lemmas only, so entries that are inflected forms of another entry are skipped.
  Such entries have `form_of` on their senses and a `form-of` tag (for example
  *pies*, "second-person singular present active subjunctive of *piō*").
  Entries have `word`, `pos`, `senses[].glosses`, `sounds[].ipa` with
  `sounds[].tags`, and `etymology_text` / `etymology_templates`; not all
  entries have every field.
- Greek (`scripts/import_wiktionary_greek.py`) uses the same scope and code. It
  imports the eight Greek languages that have entries of their own: Ancient
  Greek `grc`, Greek `el`, Mycenaean Greek `gmy`, Proto-Hellenic `grk-pro`,
  Pontic `pnt`, Tsakonian `tsd`, Cappadocian `cpg` and Yevanic `yej`. Dialect
  labels such as Koine (`grc-koi`) and Attic (`grc-att`), and Pre-Greek
  (`qsb-grc`), have no entries; they appear only as etymology languages.
  Mycenaean entries are headed in Linear B script, with the romanization left
  out. Proto-Hellenic page_refs point at `Reconstruction:Proto-Hellenic/...`.
- Etymology templates of the newer `ety` and `etymon` kinds (and `af`, `affix`,
  `root`, `uder`) are not imported for either language; the importer prints how
  many it skipped. `ety` alone is about 14,000 templates in the Greek entries,
  so a follow-up could add it.
- All Wiktionary languages share the one dump source row. The importers'
  "already imported" check is therefore per language, not per source.
- Pronunciation varieties (for example Classical and Ecclesiastical) go in
  `pronunciation.variety`.
- Every imported row uses this source, and Wiktionary's glosses are kept as
  written.
