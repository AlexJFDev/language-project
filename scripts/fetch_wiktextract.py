"""Download the kaikki.org raw Wiktionary dump into raw/ and record what we got.

    python3 scripts/fetch_wiktextract.py [--sha256 HEX]

kaikki.org overwrites this file about weekly, so the URL cannot be pinned.
Pass --sha256 to fail unless the download matches the dump a source row refers
to. Writes raw/wiktextract-meta.json with the headers, fetch time and checksum.
Resumes an interrupted download. Standard library only.
"""
import argparse
import gzip
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz"
RAW = Path(__file__).resolve().parent.parent / "raw"
DEST = RAW / "raw-wiktextract-data.jsonl.gz"
META = RAW / "wiktextract-meta.json"
CHUNK = 1 << 20


def head():
    with urllib.request.urlopen(urllib.request.Request(URL, method="HEAD")) as r:
        return {
            "content_length": int(r.headers["Content-Length"]),
            "last_modified": r.headers.get("Last-Modified"),
            "etag": r.headers.get("ETag"),
        }


def download(size):
    part = DEST.with_name(DEST.name + ".part")
    have = part.stat().st_size if part.exists() else 0
    if have > size:
        part.unlink()
        have = 0
    if have < size:
        req = urllib.request.Request(URL, headers={"Range": f"bytes={have}-"})
        with urllib.request.urlopen(req) as r:
            if have and r.status != 206:
                have = 0  # server ignored the range; start over
            with part.open("ab" if have else "wb") as f:
                while chunk := r.read(CHUNK):
                    f.write(chunk)
    if part.stat().st_size != size:
        raise SystemExit(f"{part.name}: size {part.stat().st_size} != expected {size}")
    part.replace(DEST)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def gzip_ok(path):
    try:
        with gzip.open(path) as f:
            while f.read(CHUNK):
                pass
    except (OSError, EOFError):
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sha256", help="expected checksum; exit 1 if the file differs")
    args = ap.parse_args()

    RAW.mkdir(exist_ok=True)
    meta = head()
    meta["url"] = URL
    meta["fetched_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if DEST.exists() and DEST.stat().st_size == meta["content_length"]:
        print(f"{DEST.name} already present; checking it")
    else:
        print(f"downloading {meta['content_length']:,} bytes to {DEST}")
        download(meta["content_length"])

    meta["sha256"] = sha256(DEST)
    if not gzip_ok(DEST):
        raise SystemExit(f"{DEST.name} is not a valid gzip file")
    META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"sha256 {meta['sha256']}\nwrote {META}")

    if args.sha256 and args.sha256.lower() != meta["sha256"]:
        print("checksum differs from --sha256: kaikki.org has probably published a "
              "newer build, so this is not the dump the source row records.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
