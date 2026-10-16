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

## Notes for importers

- Latin entries have `lang_code` `la`. The scope of the first import is
  lemmas only, so entries that are inflected forms of another entry are skipped.
  Such entries have `form_of` on their senses and a `form-of` tag (for example
  *pies*, "second-person singular present active subjunctive of *piō*").
  Entries have `word`, `pos`, `senses[].glosses`, `sounds[].ipa` with
  `sounds[].tags`, and `etymology_text` / `etymology_templates`; not all
  entries have every field.
- Pronunciation varieties (for example Classical and Ecclesiastical) go in
  `pronunciation.variety`.
- Every imported row uses this source, and Wiktionary's glosses are kept as
  written.
