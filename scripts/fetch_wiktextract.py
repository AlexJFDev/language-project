"""Download a kaikki.org file into raw/ and record what we got.

    python3 scripts/fetch_wiktextract.py [dump|modules] [--sha256 HEX]

dump     raw-wiktextract-data.jsonl.gz, all languages (about 3GB)
modules  wiktionary-modules.tar.gz, Wiktionary's Lua modules (about 90MB)

kaikki.org overwrites these files about weekly, so the URL cannot be pinned.
Pass --sha256 to fail unless the download matches the build a source row
refers to. Writes a *-meta.json next to the file in raw/ with the headers,
fetch time and checksum. Resumes an interrupted download.
Standard library only; the shared code is in scripts/kaikki.py.
"""
import argparse
import json
import sys
from datetime import datetime, timezone

import kaikki


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("which", nargs="?", default="dump", choices=sorted(kaikki.TARGETS))
    ap.add_argument("--sha256", help="expected checksum; exit 1 if the file differs")
    args = ap.parse_args()
    t = kaikki.TARGETS[args.which]

    kaikki.RAW.mkdir(exist_ok=True)
    meta = kaikki.head(t.url)
    meta["url"] = t.url
    meta["fetched_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if t.dest.exists() and t.dest.stat().st_size == meta["content_length"]:
        print(f"{t.dest.name} already present; checking it")
    else:
        print(f"downloading {meta['content_length']:,} bytes to {t.dest}")
        kaikki.download(t.url, t.dest, meta["content_length"])

    meta["sha256"] = kaikki.sha256(t.dest)
    if not kaikki.gzip_ok(t.dest):
        raise SystemExit(f"{t.dest.name} is not a valid gzip file")
    t.meta.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"sha256 {meta['sha256']}\nwrote {t.meta}")

    if args.sha256 and args.sha256.lower() != meta["sha256"]:
        print("checksum differs from --sha256: kaikki.org has probably published a "
              "newer build, so this is not the file the source row records.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
