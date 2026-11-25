"""Build the public checkout and add affiliate tracking to each HTML page."""
import shutil
from pathlib import Path

from visuales_editoriales import aplicar_visuales


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
        html = aplicar_visuales(page.relative_to(output).as_posix(), html.decode()).encode()
        script = b'<script src="/js/affiliate-clicks.js" defer></script>'
        page.write_bytes(html.replace(b"</body>", script + b"\n</body>", 1))


if __name__ == "__main__":
    main()
