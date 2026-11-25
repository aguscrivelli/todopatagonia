"""Build the public checkout and add affiliate tracking to each HTML page."""
import shutil
from pathlib import Path


def main():
    output = Path("_public")
    shutil.copytree(
        ".", output, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(".git", ".github", "_public", "scripts", "README.md"),
    )
    for page in output.rglob("*.html"):
        html = page.read_bytes()
        if b"</body>" not in html:
            raise ValueError(f"Falta el cierre de body en {page}")
        script = b'<script src="/js/affiliate-clicks.js" defer></script>'
        page.write_bytes(html.replace(b"</body>", script + b"\n</body>", 1))


if __name__ == "__main__":
    main()
