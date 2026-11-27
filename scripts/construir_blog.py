"""Arma los artículos del blog en ES, EN y PT a partir de contenido/blog/*.txt.

Cada archivo tiene una cabecera común (destino, foto, fecha) y una sección por
idioma (=== es / === en / === pt). Todas las versiones usan el mismo slug, así
el selector de idioma y los hreflang apuntan a páginas que existen.

Uso: python scripts/construir_blog.py
"""
import json
import sys
import types
from datetime import date
from pathlib import Path

# generar_articulo importa librerías que acá no hacen falta.
sys.modules.setdefault("anthropic", types.ModuleType("anthropic"))
_slug = types.ModuleType("slugify")
_slug.slugify = lambda *a, **k: ""
sys.modules.setdefault("slugify", _slug)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generar_articulo import BOOKING_AFFILIATE, GYG_AFFILIATE, IDIOMAS, get_template_articulo  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CONTENIDO = RAIZ / "contenido" / "blog"
MESES = {
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
           "septiembre", "octubre", "noviembre", "diciembre"],
    "pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
           "setembro", "outubro", "novembro", "dezembro"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
}
FOTO = {"es": "Foto", "en": "Photo", "pt": "Foto"}


def leer(ruta):
    cabecera, *bloques = ruta.read_text(encoding="utf-8").split("\n=== ")
    meta = dict(l.split(": ", 1) for l in cabecera.strip().splitlines() if ": " in l)
    idiomas = {}
    for bloque in bloques:
        lang, resto = bloque.split("\n", 1)
        campos, cuerpo = resto.split("\n---\n", 1)
        datos = dict(l.split(": ", 1) for l in campos.strip().splitlines())
        datos["body"] = cuerpo.strip()
        idiomas[lang.strip()] = datos
    return ruta.stem, meta, idiomas


def fecha_texto(iso, lang):
    d = date.fromisoformat(iso)
    mes = MESES[lang][d.month - 1]
    return f"{mes} {d.day}, {d.year}" if lang == "en" else f"{d.day} de {mes} de {d.year}"


def hero(meta, lang, titulo):
    return f"""<figure class="article-hero-image">
          <img src="{meta['image']}" alt="{titulo}" loading="eager">
          <figcaption>{FOTO[lang]}: <a href="{meta['image_source']}" target="_blank" rel="noopener">{meta['image_author']}</a> · Wikimedia Commons</figcaption>
        </figure>"""


def main():
    articulos = [leer(p) for p in sorted(CONTENIDO.glob("*.txt"))]
    # Si el archivo no trae foto, se usa la que ya figura en el índice en español.
    indice_es = {a["slug"]: a for a in json.loads((RAIZ / "blog" / "articles.json").read_text())}
    for slug, meta, _ in articulos:
        previo = indice_es.get(slug, {})
        meta.setdefault("image", previo.get("image_url", ""))
        meta.setdefault("image_author", previo.get("image_author", ""))
        meta.setdefault("image_source", previo.get("image_source", ""))
        meta.setdefault("emoji", previo.get("emoji", "🏔️"))
        meta.setdefault("date", previo.get("date", date.today().isoformat()))
    por_slug = {s: (m, i) for s, m, i in articulos}
    for slug, meta, idiomas in articulos:
        for lang, d in idiomas.items():
            cfg = IDIOMAS[lang]
            carpeta = RAIZ / cfg["blog_dir"]
            prefijo = "../" * len(Path(cfg["blog_dir"]).parts)
            html = get_template_articulo(cfg, slug, prefijo).format(
                slug=slug, title=d["title"], meta_description=d["meta"], excerpt=d["excerpt"],
                category=d["category"], date=fecha_texto(meta["date"], lang),
                destination=meta["destination"],
                destination_encoded=meta["destination"].replace(" ", "+"),
                read_time=d.get("read_time", 5), body_html=d["body"],
                booking_affiliate=BOOKING_AFFILIATE, gyg_affiliate=GYG_AFFILIATE,
                hero_image_html=hero(meta, lang, d["title"]),
                og_image_tag=f'<meta property="og:image" content="{meta["image"]}">',
            )
            carpeta.mkdir(parents=True, exist_ok=True)
            (carpeta / f"{slug}.html").write_text(html, encoding="utf-8")
            print(f"✅ {cfg['blog_dir']}/{slug}.html")

    # Índices: el orden lo manda el índice en español.
    orden = [a["slug"] for a in json.loads((RAIZ / "blog" / "articles.json").read_text())]
    orden += [s for s in por_slug if s not in orden]
    for lang, cfg in IDIOMAS.items():
        ruta = RAIZ / cfg["blog_dir"] / "articles.json"
        previos = {a["slug"]: a for a in json.loads(ruta.read_text())} if ruta.exists() else {}
        salida = []
        for slug in orden:
            if slug in por_slug and lang in por_slug[slug][1]:
                meta, idiomas = por_slug[slug]
                d = idiomas[lang]
                salida.append({
                    "slug": slug, "title": d["title"], "excerpt": d["excerpt"],
                    "category": d["category"], "emoji": meta["emoji"], "date": meta["date"],
                    "destination": meta["destination"], "lang": lang,
                    "image_url": meta["image"], "image_author": meta["image_author"],
                    "image_source": meta["image_source"],
                })
            elif slug in previos and (RAIZ / cfg["blog_dir"] / f"{slug}.html").exists():
                salida.append(previos[slug])
        ruta.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ {cfg['blog_dir']}/articles.json ({len(salida)} artículos)")


if __name__ == "__main__":
    main()
