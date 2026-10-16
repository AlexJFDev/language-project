"""Build the static site for GitHub Pages.

    python3 scripts/build_site.py <outdir>

Writes work.db (built from data/*.csv), metadata.yml and index.html into
<outdir>. index.html redirects to Datasette Lite (Datasette running in the
visitor's browser), pointed at the db and metadata next to it. The URLs are
computed in the browser, so the output does not depend on where it is hosted.
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import db  # noqa: E402

INDEX = """<!doctype html>
<meta charset="utf-8">
<title>Ancient Lexicon Database</title>
<p>Loading the database browser&hellip;</p>
<script>
  const base = new URL(".", location.href).href;
  location.replace("https://lite.datasette.io/?url=" + encodeURIComponent(base + "work.db") +
    "&metadata=" + encodeURIComponent(base + "metadata.yml"));
</script>
<noscript><p>This page needs JavaScript to open the database browser.</p></noscript>
"""


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    out = Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    path = out / "work.db"
    path.unlink(missing_ok=True)
    con = db.connect(path)
    db.load(con)
    problems = db.check(con)
    con.close()
    if problems:
        print("\n".join(problems))
        return 1
    shutil.copy(HERE / "browse_metadata.yml", out / "metadata.yml")
    (out / "index.html").write_text(INDEX, encoding="utf-8")
    print(f"built site in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
