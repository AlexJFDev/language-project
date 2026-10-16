"""Browse the database in a web browser (read-only), using Datasette.

    python3 scripts/browse.py [port]

Rebuilds work.db from data/*.csv, then serves it at http://127.0.0.1:<port>
(default 8001). Edits to the CSVs show up after restarting. Needs the
dependency in requirements.txt (pip install -r requirements.txt).
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import db  # noqa: E402


def main(argv):
    exe = shutil.which("datasette") or str(Path(sys.executable).parent / "datasette")
    if not Path(exe).exists():
        raise SystemExit("datasette not found; run: pip install -r requirements.txt")
    if db.main(["db.py", "load", str(db.DEFAULT_DB)]):
        return 1
    port = argv[1] if len(argv) > 1 else "8001"
    return subprocess.call([
        exe, "serve", "--immutable", str(db.DEFAULT_DB),
        "--metadata", str(HERE / "browse_metadata.yml"),
        "--port", port,
    ])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
