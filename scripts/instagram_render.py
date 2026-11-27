"""Genera las imágenes de Instagram a partir de instagram/cola.json.

- Busca fotos libres en Wikimedia Commons (por nombre de archivo o por búsqueda).
- Arma carruseles de 1080x1350 con texto encima, o fotos sueltas con marca.
- Guarda las imágenes en ig/<id>/N.jpg (se publican en el sitio con el deploy).
- Registra créditos y rutas en instagram/medios.json.
- Regenera ig.html, la página del link de la bio.

Uso: python scripts/instagram_render.py [--forzar ID]
"""
import io
import json
import re
import sys
import textwrap
from html import escape, unescape
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
COLA = RAIZ / "instagram" / "cola.json"
MEDIOS = RAIZ / "instagram" / "medios.json"
SALIDA = RAIZ / "ig"
ANCHO, ALTO = 1080, 1350
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "TodoPatagoniaBot/1.0 (https://todopatagonia.com; bot@todopatagonia.com)"}

FUENTES_BOLD = [
    "/tmp/fuentes/Montserrat-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FUENTES_REG = [
    "/tmp/fuentes/Montserrat-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
CELESTE = (125, 196, 230)
BLANCO = (255, 255, 255)


def fuente(tamano, negrita=False):
    for ruta in FUENTES_BOLD if negrita else FUENTES_REG:
        if Path(ruta).exists():
            return ImageFont.truetype(ruta, tamano)
    return ImageFont.load_default(tamano)


def limpiar_html(texto):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", texto or ""))).strip()


def info_commons(params):
    base = {
        "action": "query", "format": "json", "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1600,
    }
    r = requests.get(API, params={**base, **params}, headers=UA, timeout=30)
    r.raise_for_status()
    paginas = r.json().get("query", {}).get("pages", {})
    return sorted(paginas.values(), key=lambda p: p.get("index", 0))


def elegir_foto(foto, usadas):
    """Devuelve dict con url, credito, fuente y titulo de una foto de Commons."""
    if foto.get("archivo"):
        paginas = info_commons({"titles": "File:" + foto["archivo"]})
    else:
        paginas = info_commons({
            "generator": "search", "gsrnamespace": 6, "gsrlimit": 20,
            "gsrsearch": f"filetype:bitmap {foto['buscar']}",
        })
    for p in paginas:
        ii = (p.get("imageinfo") or [{}])[0]
        if not ii or p["title"] in usadas:
            continue
        if ii.get("mime") != "image/jpeg" or ii.get("width", 0) < 1200:
            continue
        if not foto.get("archivo") and ii["width"] < ii["height"] * 0.7:
            continue
        meta = ii.get("extmetadata", {})
        autor = limpiar_html(meta.get("Artist", {}).get("value")) or "Autor desconocido"
        licencia = limpiar_html(meta.get("LicenseShortName", {}).get("value")) or "licencia libre"
        return {
            "titulo": p["title"],
            "url": ii.get("thumburl") or ii["url"],
            "fuente": ii.get("descriptionurl", ""),
            "credito": f"{autor[:80]} / Wikimedia Commons ({licencia})",
        }
    raise RuntimeError(f"No encontré foto apta para {foto}")


def bajar(url):
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGB")


def recorte(img):
    return ImageOps.fit(img, (ANCHO, ALTO), Image.LANCZOS, centering=(0.5, 0.45))


def degradado(img, desde=0.35, opacidad=235):
    capa = Image.new("L", (1, ALTO))
    for y in range(ALTO):
        t = max(0.0, (y / ALTO - desde) / (1 - desde))
        capa.putpixel((0, y), int(opacidad * min(1.0, t * 1.3)))
    capa = capa.resize((ANCHO, ALTO))
    negro = Image.new("RGB", (ANCHO, ALTO), (8, 18, 28))
    return Image.composite(negro, img, capa)


def escribir(d, texto, x, y, tam, negrita, ancho_chars, color=BLANCO, interlineado=1.25):
    f = fuente(tam, negrita)
    for linea in textwrap.wrap(texto, ancho_chars):
        d.text((x, y), linea, font=f, fill=color)
        y += int(tam * interlineado)
    return y


def pie(d, n=None, total=None):
    d.text((70, ALTO - 95), "TODOPATAGONIA.COM", font=fuente(30, True), fill=BLANCO)
    if n and total:
        txt = f"{n}/{total}"
        f = fuente(30, True)
        w = d.textlength(txt, font=f)
        d.text((ANCHO - 70 - w, ALTO - 95), txt, font=f, fill=BLANCO)


def alto_texto(texto, tam, ancho_chars, interlineado=1.25):
    return len(textwrap.wrap(texto, ancho_chars)) * int(tam * interlineado)


def portada(foto, slide, total):
    img = degradado(recorte(foto), 0.3)
    d = ImageDraw.Draw(img)
    titulo_h = alto_texto(slide["titulo"], 86, 18, 1.12)
    y = ALTO - 230 - titulo_h - (alto_texto(slide.get("texto", ""), 40, 40) if slide.get("texto") else 0)
    if slide.get("antetitulo"):
        d.text((70, y - 70), slide["antetitulo"].upper(), font=fuente(34, True), fill=CELESTE)
    y = escribir(d, slide["titulo"], 70, y, 86, True, 18, interlineado=1.12)
    if slide.get("texto"):
        escribir(d, slide["texto"], 70, y + 20, 40, False, 40)
    if total > 1:
        f = fuente(30, True)
        txt = "Deslizá →"
        d.text((ANCHO - 70 - d.textlength(txt, font=f), 80), txt, font=f, fill=BLANCO)
    pie(d)
    return img


def interior(foto, slide, n, total):
    fondo = recorte(foto).filter(ImageFilter.GaussianBlur(18))
    fondo = Image.blend(fondo, Image.new("RGB", (ANCHO, ALTO), (8, 18, 28)), 0.72)
    d = ImageDraw.Draw(fondo)
    y = 190
    if slide.get("numero"):
        d.text((70, y), str(slide["numero"]), font=fuente(150, True), fill=CELESTE)
        y += 200
    y = escribir(d, slide["titulo"], 70, y, 66, True, 24, interlineado=1.15)
    d.rectangle((70, y + 25, 190, y + 33), fill=CELESTE)
    escribir(d, slide.get("texto", ""), 70, y + 70, 44, False, 38, interlineado=1.35)
    pie(d, n, total)
    return fondo


def cierre(foto, slide, n, total):
    img = recorte(foto).filter(ImageFilter.GaussianBlur(6))
    img = Image.blend(img, Image.new("RGB", (ANCHO, ALTO), (8, 18, 28)), 0.62)
    d = ImageDraw.Draw(img)
    y = 380
    y = escribir(d, slide.get("titulo", "La guía completa está en el sitio"), 70, y, 72, True, 22, interlineado=1.15)
    y = escribir(d, slide.get("texto", "todopatagonia.com"), 70, y + 40, 46, False, 36, color=CELESTE)
    escribir(d, "Link en la bio · Guardá este post para tu viaje", 70, y + 60, 38, False, 40)
    pie(d, n, total)
    return img


def foto_suelta(foto, post):
    img = recorte(foto)
    if post.get("rotulo"):
        img = degradado(img, 0.6, 200)
    d = ImageDraw.Draw(img)
    if post.get("rotulo"):
        d.text((70, ALTO - 170), post["rotulo"].upper(), font=fuente(40, True), fill=BLANCO)
    d.text((70, ALTO - 95), "TODOPATAGONIA.COM", font=fuente(28, True), fill=BLANCO)
    return img


def renderizar(post, foto):
    if post["tipo"] == "foto":
        return [foto_suelta(foto, post)]
    slides = post["slides"]
    total = len(slides) + 1
    imgs = [portada(foto, slides[0], total)]
    for i, s in enumerate(slides[1:], start=2):
        imgs.append(interior(foto, s, i, total))
    imgs.append(cierre(foto, post.get("cierre", {}), total, total))
    return imgs


def pagina_bio():
    """ig.html: página del link de la bio, con UTM para medir el tráfico."""
    utm = "utm_source=instagram&utm_medium=bio"
    destinos = json.loads((RAIZ / "data" / "destinos.json").read_text())["activos"]
    links = [(f"{d['emoji']} {d['nombre']}", f"/destinos/{d['slug']}.html") for d in destinos]
    links += [("✈️ Cómo llegar", "/como-llegar.html"), ("🥾 Actividades", "/actividades.html")]
    articulos = json.loads((RAIZ / "blog" / "articles.json").read_text())
    for a in articulos[:8]:
        if (RAIZ / "blog" / f"{a['slug']}.html").exists():
            links.append((f"{a['emoji']} {a['title']}", f"/blog/{a['slug']}.html"))
    botones = "\n".join(
        f'    <a class="b" href="{escape(url)}?{utm}">{escape(txt)}</a>' for txt, url in links
    )
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TodoPatagonia · Guías para tu viaje</title>
<meta name="robots" content="noindex">
<style>
body{{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#08121c;color:#fff}}
main{{max-width:520px;margin:0 auto;padding:40px 20px 60px}}
h1{{font-size:26px;margin:0 0 6px}} p{{color:#9fb3c4;margin:0 0 28px}}
.b{{display:block;padding:16px 18px;margin:0 0 12px;border-radius:12px;background:#132636;color:#fff;
text-decoration:none;font-weight:600;border:1px solid #1f3a50}}
.b:hover{{background:#1b3448}} .home{{background:#7dc4e6;color:#08121c;border-color:#7dc4e6}}
</style>
</head>
<body>
<main>
  <h1>TodoPatagonia</h1>
  <p>Guías para planificar tu viaje a la Patagonia argentina y chilena.</p>
    <a class="b home" href="/?{utm}">🏔️ Ir al sitio</a>
{botones}
</main>
</body>
</html>
"""
    (RAIZ / "ig.html").write_text(html)


def main():
    forzar = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--forzar" else None
    cola = json.loads(COLA.read_text())
    medios = json.loads(MEDIOS.read_text()) if MEDIOS.exists() else {}
    usadas = {m["titulo"] for m in medios.values()}
    errores = 0
    for post in cola:
        pid = post["id"]
        hecho = pid in medios and all((RAIZ / r).exists() for r in medios[pid]["imagenes"])
        if hecho and pid != forzar:
            continue
        try:
            elegida = elegir_foto(post["foto"], usadas - ({medios[pid]["titulo"]} if pid in medios else set()))
            imgs = renderizar(post, bajar(elegida["url"]))
        except Exception as e:  # sigue con los demás posts
            print(f"⚠️  {pid}: {e}")
            errores += 1
            continue
        carpeta = SALIDA / pid
        carpeta.mkdir(parents=True, exist_ok=True)
        rutas = []
        for i, img in enumerate(imgs, start=1):
            ruta = carpeta / f"{i}.jpg"
            img.save(ruta, "JPEG", quality=86, optimize=True, progressive=True)
            rutas.append(ruta.relative_to(RAIZ).as_posix())
        medios[pid] = {**elegida, "imagenes": rutas}
        usadas.add(elegida["titulo"])
        print(f"✅ {pid}: {len(rutas)} imagen(es) · {elegida['titulo']}")
    MEDIOS.write_text(json.dumps(medios, ensure_ascii=False, indent=2) + "\n")
    pagina_bio()
    print(f"Listo. {len(medios)} posts con imágenes, {errores} con problemas.")


if __name__ == "__main__":
    main()
