"""Load data/*.csv into a temporary SQLite database, or export it back.

    python3 scripts/db.py load [db]     build db from schema + CSVs, then check
    python3 scripts/db.py export [db]   write the db back to data/*.csv
    python3 scripts/db.py check         load into memory, report problems
    python3 scripts/db.py roundtrip     load then export; fail if data/ changes

The CSVs in git are the source of truth; the db is disposable.
Export is deterministic: rows sorted by id, columns in schema order,
UTF-8, LF line endings.
"""
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCHEMA = ROOT / "schema" / "schema.sql"
DEFAULT_DB = ROOT / "work.db"


def connect(path):
    con = sqlite3.connect(path)
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    return con


def tables(con):
    # sqlite_master lists tables in creation order, which is dependency order
    return [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY rowid")]


def columns(con, table):
    return [r[1] for r in con.execute(f"PRAGMA table_info({table})")]


def load(con):
    for t in tables(con):
        cols = columns(con, t)
        path = DATA / f"{t}.csv"
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header != cols:
                raise SystemExit(f"{path.name}: header {header} != schema {cols}")
            rows = [[v if v != "" else None for v in r] for r in reader]
        con.executemany(
            f"INSERT INTO {t} VALUES ({','.join('?' * len(cols))})", rows)
    con.commit()


def check(con):
    problems = [f"{t}: row {rowid} has a bad reference to {parent}"
                for t, rowid, parent, _ in con.execute("PRAGMA foreign_key_check")]
    return problems


def export(con):
    DATA.mkdir(exist_ok=True)
    for t in tables(con):
        cols = columns(con, t)
        with (DATA / f"{t}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(cols)
            for row in con.execute(f"SELECT * FROM {t} ORDER BY id"):
                w.writerow("" if v is None else v for v in row)


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    path = Path(argv[2]) if len(argv) > 2 else DEFAULT_DB
    if cmd in ("load", "export"):
        path.unlink(missing_ok=True) if cmd == "load" else None
    if cmd == "load":
        con = connect(path)
        load(con)
        problems = check(con)
        print("\n".join(problems) or f"loaded into {path}")
        return 1 if problems else 0
    if cmd == "export":
        export(connect(path) if not path.exists() else sqlite3.connect(path))
        return 0
    if cmd == "check":
        con = connect(":memory:")
        load(con)
        problems = check(con)
        print("\n".join(problems) or "ok")
        return 1 if problems else 0
    if cmd == "roundtrip":
        before = {p: p.read_bytes() for p in DATA.glob("*.csv")}
        con = connect(":memory:")
        load(con)
        export(con)
        after = {p: p.read_bytes() for p in DATA.glob("*.csv")}
        changed = sorted(p.name for p in after if before.get(p) != after[p])
        print("changed: " + ", ".join(changed) if changed else "no diff")
        return 1 if changed else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
