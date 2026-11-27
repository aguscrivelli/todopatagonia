"""Build the public checkout and add affiliate tracking to each HTML page."""
import shutil
from pathlib import Path

from seo import procesar as aplicar_seo
from traslados import agregar_traslados
from verificar_idiomas import revisar as revisar_idiomas
from visuales_editoriales import aplicar_visuales


def main():
    output = Path("_public")
    shutil.copytree(
        ".", output, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(".git", ".github", "_public", "scripts", "instagram", "README.md"),
    )
    for page in output.rglob("*.html"):
        if page.name.startswith("google") and page.parent == output:
            continue  # archivo de verificación de Search Console: va tal cual
        html = page.read_bytes()
        if b"</body>" not in html:
            raise ValueError(f"Falta el cierre de body en {page}")
        path = page.relative_to(output).as_posix()
        html = aplicar_visuales(path, html.decode())
        html = agregar_traslados(path, html).encode()
        script = b'<script src="/js/affiliate-clicks.js?v=2" defer></script>'
        page.write_bytes(html.replace(b"</body>", script + b"\n</body>", 1))
    aplicar_seo(output)

    # Regla de idiomas: si alguna página mezcla idiomas, no se publica.
    problemas = revisar_idiomas(output)
    if problemas:
        for ruta, otro, texto in problemas:
            print(f"  {ruta} [{otro}] {texto}")
        raise SystemExit(f"❌ {len(problemas)} textos en otro idioma: corregilos antes de publicar "
                         "(o agregá la excepción en contenido/idiomas_permitidos.txt).")
    print("Idiomas: sin mezclas.")


if __name__ == "__main__":
    main()
