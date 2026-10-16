"""Download kaikki.org files into raw/ and tie them to a source row.

kaikki.org overwrites its files about weekly and keeps no dated copies, so a
download is only repeatable if we record its sha256. Each file we use has a
`source` row whose notes hold that checksum (`sha256 <hex>`); `verify` checks a
local file against it, and importers call it before reading anything.

To use another kaikki.org file: add a Target below, register its source row
(see docs/sources/), and fetch it with scripts/fetch_wiktextract.py.
Standard library only.
"""
import csv
import gzip
import hashlib
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
CHUNK = 1 << 20


@dataclass(frozen=True)
class Target:
    url: str
    dest: Path
    meta: Path       # where the headers, fetch time and checksum are recorded
    source_id: str   # the source row that pins this file's checksum


TARGETS = {
    "dump": Target(
        "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz",
        RAW / "raw-wiktextract-data.jsonl.gz",
        RAW / "wiktextract-meta.json",
        "src-wiktionary-en-20260902"),
    "modules": Target(
        "https://kaikki.org/dictionary/wiktionary-modules.tar.gz",
        RAW / "wiktionary-modules.tar.gz",
        RAW / "wiktionary-modules-meta.json",
        "src-wiktionary-modules-20261003"),
}


def head(url):
    with urllib.request.urlopen(urllib.request.Request(url, method="HEAD")) as r:
        return {
            "content_length": int(r.headers["Content-Length"]),
            "last_modified": r.headers.get("Last-Modified"),
            "etag": r.headers.get("ETag"),
        }


def download(url, dest, size):
    """Fetch url to dest, resuming a partial .part file if there is one."""
    part = dest.with_name(dest.name + ".part")
    have = part.stat().st_size if part.exists() else 0
    if have > size:
        part.unlink()
        have = 0
    if have < size:
        req = urllib.request.Request(url, headers={"Range": f"bytes={have}-"})
        with urllib.request.urlopen(req) as r:
            if have and r.status != 206:
                have = 0  # server ignored the range; start over
            with part.open("ab" if have else "wb") as f:
                while chunk := r.read(CHUNK):
                    f.write(chunk)
    if part.stat().st_size != size:
        raise SystemExit(f"{part.name}: size {part.stat().st_size} != expected {size}")
    part.replace(dest)


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


def expected_sha256(source_id):
    """The checksum recorded on a source row's notes."""
    with (ROOT / "data" / "source.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["id"] == source_id:
                m = re.search(r"sha256 ([0-9a-f]{64})", row["notes"])
                if m:
                    return m.group(1)
    raise SystemExit(f"no sha256 found on source row {source_id}")


def verify(target):
    """Exit unless the local file is the build its source row records."""
    if not target.dest.exists():
        raise SystemExit(f"{target.dest} is missing; run scripts/fetch_wiktextract.py")
    if sha256(target.dest) != expected_sha256(target.source_id):
        raise SystemExit(f"{target.dest.name} differs from source row "
                         f"{target.source_id}; refusing to use it")
