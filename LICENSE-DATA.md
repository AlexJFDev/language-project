# Data license

This applies to the contents of `data/` (the CSV files). The code in
`scripts/` and `schema/` is under the MIT License; see `LICENSE`.

## The license of a row is the license of its source

The data is a collection of claims, each attributed to a source. Every claim
row points to a row in `data/source.csv`, and that row's `license` column says
what license the claim is under. Rows are not all under one license.

| Where the row comes from | License |
| --- | --- |
| Original contributions: rows with `obtained` of `contributed` or `derived`, and the `source` rows themselves | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) (public domain dedication) |
| Derived from Wiktionary, including the kaikki.org / wiktextract dumps | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Any other source | Whatever its `source.license` says |

Wiktionary content is licensed CC BY-SA, which is share-alike: material copied
or adapted from it must stay under CC BY-SA and cannot be relicensed as CC0.
That is why a row's license follows its source rather than the project.

## Using the data

- **Attribution.** For CC BY-SA rows, credit the source (the row's `source_id`
  gives it, and `source.url` links to it) and keep the license on any
  redistributed copy. CC0 rows need no credit, though it is appreciated.
- **Share-alike.** If you redistribute or adapt CC BY-SA rows, release those
  rows under CC BY-SA 4.0 or a compatible license.
- **Taking only the unrestricted part.** Filter rows by joining on `source_id`
  and keeping those whose source license is CC0. Do not assume a whole table
  is CC0 just because it contains CC0 rows.
- **Restricted sources.** Where `source.allows_bulk_reuse` is `no` or
  `unknown`, check that source's terms before redistributing its rows.

## Disclaimer

Data is provided "as is" without warranty of any kind. This file describes how
the project intends to license its data and is not legal advice.
