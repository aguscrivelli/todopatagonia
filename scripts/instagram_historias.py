"""Genera las imágenes en formato historia (1080x1920).

1. Una historia por post (ig/<id>/historia.jpg) que avisa del post nuevo.
   La publica sola instagram_publicar.py después del post de la tarde.
2. El kit de destacadas (ig/destacadas/): una historia y una portada por
   destino, más una página para descargarlas desde el celular.

Corre después de instagram_render.py (usa las fotos de instagram/medios.json).
"""
import json
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from instagram_render import (
    BLANCO, CELESTE, MEDIOS, COLA, RAIZ, bajar, escribir, fuente, alto_texto,
)

AN, AL = 1080, 1920
AZUL = (26, 58, 92)
AZUL_CLARO = (45, 106, 159)
NARANJA = (212, 101, 10)
CARPETA_DEST = RAIZ / "ig" / "destacadas"

DESTACADAS = [
    {"slug": "calafate", "nombre": "Calafate", "post": "01-perito-moreno-claves", "icono": "glaciar",
     "titulo": "El Calafate", "texto": "Perito Moreno, navegaciones y caminatas sobre el hielo.",
     "link": "/destinos/el-calafate.html"},
    {"slug": "chalten", "nombre": "Chaltén", "post": "02-fitz-roy", "icono": "cerro",
     "titulo": "El Chaltén", "texto": "La Capital Nacional del Trekking, a los pies del Fitz Roy.",
     "link": "/destinos/el-chalten.html"},
    {"slug": "ushuaia", "nombre": "Ushuaia", "post": "26-faro-eclaireurs", "icono": "faro",
     "titulo": "Ushuaia", "texto": "Canal Beagle, pingüinos y el Parque Nacional Tierra del Fuego.",
     "link": "/destinos/ushuaia.html"},
    {"slug": "bariloche", "nombre": "Bariloche", "post": "24-campanario", "icono": "lagos",
     "titulo": "Bariloche", "texto": "Lagos, cerros y bosques. Un destino para todo el año.",
     "link": "/destinos/bariloche.html"},
    {"slug": "valdes", "nombre": "Valdés", "post": "04-ballena-valdes", "icono": "ballena",
     "titulo": "Península Valdés", "texto": "Ballenas, orcas, pingüinos y lobos marinos.",
     "link": "/destinos/peninsula-valdes.html"},
    {"slug": "paine", "nombre": "Paine", "post": "06-torres-del-paine", "icono": "torres",
     "titulo": "Torres del Paine", "texto": "El parque más famoso de la Patagonia chilena.",
     "link": "/destinos/torres-del-paine.html"},
    {"slug": "tips", "nombre": "Tips", "post": "13-que-llevar", "icono": "brujula",
     "titulo": "Tips de viaje", "texto": "Cuándo ir, cómo llegar y qué llevar a la Patagonia.",
     "link": "/como-llegar.html"},
]


def oscurecer_abajo(img, desde=0.45, opacidad=235):
    capa = Image.new("L", (1, AL))
    for y in range(AL):
        t = max(0.0, (y / AL - desde) / (1 - desde))
        capa.putpixel((0, y), int(opacidad * min(1.0, t * 1.4)))
    capa = capa.resize((AN, AL))
    return Image.composite(Image.new("RGB", (AN, AL), (8, 18, 28)), img, capa)


def flecha_arriba(d, cx, y, color=BLANCO):
    d.polygon([(cx, y), (cx - 34, y + 40), (cx + 34, y + 40)], fill=color)
    d.rectangle((cx - 9, y + 38, cx + 9, y + 95), fill=color)


def historia_post(post, foto):
    img = oscurecer_abajo(ImageOps.fit(foto, (AN, AL), Image.LANCZOS))
    d = ImageDraw.Draw(img)
    titulo = post["slides"][0]["titulo"] if post["tipo"] == "carrusel" else post.get("rotulo", "")
    y = AL - 330 - alto_texto(titulo, 84, 19, 1.12)
    d.text((80, y - 80), "NUEVO POST", font=fuente(38, True), fill=CELESTE)
    y = escribir(d, titulo, 80, y, 84, True, 19, interlineado=1.12)
    flecha_arriba(d, 110, y + 40)
    d.text((170, y + 60), "Miralo en el perfil", font=fuente(40, False), fill=BLANCO)
    return img


def historia_destacada(dest, foto):
    img = oscurecer_abajo(ImageOps.fit(foto, (AN, AL), Image.LANCZOS), 0.3, 240)
    d = ImageDraw.Draw(img)
    y = 1000
    d.text((80, y - 70), "GUÍA DE VIAJE", font=fuente(38, True), fill=CELESTE)
    y = escribir(d, dest["titulo"], 80, y, 96, True, 16, interlineado=1.1)
    y = escribir(d, dest["texto"], 80, y + 25, 46, False, 34, interlineado=1.3)
    # Debajo queda libre el espacio para el sticker de link (se agrega desde la app).
    d.text((80, y + 50), "Tocá el link para ver la guía completa", font=fuente(40, True), fill=CELESTE)
    d.text((80, AL - 300), "TODOPATAGONIA.COM", font=fuente(32, True), fill=BLANCO)
    return img


# --- Íconos de las portadas (dibujados a 3x y reducidos) ---
def icono(nombre):
    S = 3 * 1080
    img = Image.new("RGB", (S, S), AZUL)
    d = ImageDraw.Draw(img)
    c = S // 2
    B, N, C = BLANCO, NARANJA, AZUL_CLARO
    if nombre == "glaciar":
        d.polygon([(700, 1900), (900, 1250), (1050, 1500), (1250, 1050), (1450, 1450), (1650, 1000),
                   (1850, 1400), (2050, 1150), (2250, 1550), (2450, 1250), (2550, 1900)], fill=B)
        for i, y in enumerate(range(2050, 2450, 130)):
            d.line([(800 + i * 90, y), (2440 - i * 90, y)], fill=C, width=50)
    elif nombre == "cerro":
        d.polygon([(650, 2200), (1350, 1450), (1620, 800), (1900, 1450), (2600, 2200)], fill=B)
        d.ellipse((2050, 850, 2450, 1250), fill=N)
    elif nombre == "faro":
        d.polygon([(1400, 2150), (1480, 1100), (1760, 1100), (1840, 2150)], fill=B)
        def borde(y):  # la torre se ensancha hacia abajo
            k = (y - 1100) * 80 / 1050
            return 1480 - k, 1760 + k
        for y in (1350, 1750):
            (a, b), (c2, d2) = borde(y), borde(y + 180)
            d.polygon([(a, y), (b, y), (d2, y + 180), (c2, y + 180)], fill=N)
        d.rectangle((1430, 900, 1810, 1100), fill=B)
        d.polygon([(1400, 900), (1620, 700), (1840, 900)], fill=N)
        d.rectangle((1000, 2150, 2240, 2260), fill=C)
    elif nombre == "lagos":
        d.polygon([(500, 1900), (1150, 1050), (1600, 1650), (2050, 1150), (2750, 1900)], fill=B)
        for i, y in enumerate(range(2030, 2450, 130)):
            d.line([(700 + i * 90, y), (2540 - i * 90, y)], fill=C, width=50)
    elif nombre == "ballena":
        izq = [(1620, 1720), (1450, 1560), (1200, 1430), (900, 1230), (1020, 1470), (1250, 1650), (1500, 1790)]
        d.polygon(izq, fill=B)
        d.polygon([(3240 - x, y) for x, y in izq], fill=B)
        d.polygon([(1545, 1700), (1695, 1700), (1660, 2120), (1580, 2120)], fill=B)
        for i, y in enumerate(range(2150, 2500, 130)):
            d.line([(900 + i * 80, y), (2340 - i * 80, y)], fill=C, width=50)
    elif nombre == "torres":
        for x, top in ((1150, 1000), (1550, 800), (1950, 1050)):
            d.rounded_rectangle((x, top, x + 270, 2200), radius=135, fill=B)
        d.rectangle((900, 2100, 2400, 2250), fill=C)
    elif nombre == "brujula":
        d.ellipse((c - 900, c - 900, c + 900, c + 900), outline=B, width=110)
        d.polygon([(c, c - 650), (c + 180, c), (c - 180, c)], fill=N)
        d.polygon([(c, c + 650), (c + 180, c), (c - 180, c)], fill=B)
    return img.resize((1080, 1080), Image.LANCZOS)


def portada_destacada(dest):
    fondo = Image.new("RGB", (AN, AL), AZUL)
    fondo.paste(icono(dest["icono"]), (0, (AL - 1080) // 2))
    return fondo


def pagina_kit(items):
    filas = "\n".join(
        f"""<section><h2>{escape(i['nombre'])}</h2>
<div class="par"><a href="{i['portada']}" download><img src="{i['portada']}" alt="Portada {escape(i['nombre'])}"></a>
<a href="{i['historia']}" download><img src="{i['historia']}" alt="Historia {escape(i['nombre'])}"></a></div>
<p>Link para el sticker: <code>https://todopatagonia.com{i['link']}?utm_source=instagram&amp;utm_medium=historia</code></p></section>"""
        for i in items
    )
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kit de destacadas</title><meta name="robots" content="noindex">
<style>body{{margin:0;font-family:system-ui,sans-serif;background:#08121c;color:#fff}}main{{max-width:640px;margin:0 auto;padding:24px}}
.par{{display:flex;gap:10px}}.par img{{width:100%;border-radius:10px}}.par a{{flex:1}}code{{word-break:break-all;color:#7dc4e6}}
section{{margin:0 0 36px}}p{{color:#9fb3c4}}</style></head>
<body><main><h1>Kit de destacadas</h1>
<p>Tocá una imagen y guardala (mantené apretado en el celular). A la izquierda, la portada; a la derecha, la historia.</p>
{filas}
</main></body></html>
"""
    (CARPETA_DEST / "index.html").write_text(html)


def main():
    cola = {p["id"]: p for p in json.loads(COLA.read_text())}
    medios = json.loads(MEDIOS.read_text())
    cache = {}

    def foto(pid):
        if pid not in cache:
            cache[pid] = bajar(medios[pid]["url"])
        return cache[pid]

    for pid, m in medios.items():
        ruta = RAIZ / "ig" / pid / "historia.jpg"
        if pid in cola and not ruta.exists():
            try:
                historia_post(cola[pid], foto(pid)).save(ruta, "JPEG", quality=86, optimize=True)
                print(f"✅ historia {pid}")
            except Exception as e:
                print(f"⚠️  historia {pid}: {e}")
                continue
        if ruta.exists():
            m["historia"] = ruta.relative_to(RAIZ).as_posix()
    MEDIOS.write_text(json.dumps(medios, ensure_ascii=False, indent=2) + "\n")

    CARPETA_DEST.mkdir(parents=True, exist_ok=True)
    items = []
    for dest in DESTACADAS:
        h = CARPETA_DEST / f"{dest['slug']}-historia.jpg"
        p = CARPETA_DEST / f"{dest['slug']}-portada.jpg"
        try:
            if not h.exists():
                historia_destacada(dest, foto(dest["post"])).save(h, "JPEG", quality=88, optimize=True)
            if not p.exists():
                portada_destacada(dest).save(p, "JPEG", quality=92)
        except Exception as e:
            print(f"⚠️  destacada {dest['slug']}: {e}")
            continue
        items.append({**dest, "historia": f"/ig/destacadas/{h.name}", "portada": f"/ig/destacadas/{p.name}"})
        print(f"✅ destacada {dest['slug']}")
    pagina_kit(items)


if __name__ == "__main__":
    main()
