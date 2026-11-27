"""Curated photos shared across the three published locales."""
from html import escape

COMMONS = "https://commons.wikimedia.org/wiki/File:"
UPLOAD = "https://upload.wikimedia.org/wikipedia/commons/"
HERO = (
    "Torres-del-paine.jpg", "Gonzalobaeza · CC BY-SA 4.0",
    "Torres del Paine", "Torres del Paine", "Torres del Paine",
)
ACTIVIDADES = (
    (
        "Fitz_Roy_Chalten_Argentina_Todor_Bozhinov_2013.jpg", "Todor Bozhinov · CC BY-SA 3.0",
        "Trekking · Fitz Roy, El Chaltén", "Hiking · Fitz Roy, El Chaltén", "Trilhas · Fitz Roy, El Chaltén",
    ),
    (
        "153_-_Glacier_Perito_Moreno_-_Grotte_glaciaire_-_Janvier_2010.jpg", "Luc Viatour · CC BY-SA 3.0",
        "Glaciares · Perito Moreno", "Glaciers · Perito Moreno", "Glaciares · Perito Moreno",
    ),
    (
        "Tail_of_a_whale_near_Valdes_Peninsula.jpg", "Edith Schreurs · CC BY-SA 2.0",
        "Fauna · Ballena franca austral, Península Valdés", "Wildlife · Southern right whale, Valdés Peninsula",
        "Fauna · Baleia-franca-austral, Península Valdés",
    ),
)
PORTADAS = {"index.html": 2, "en/index.html": 3, "pt/index.html": 4}
PAGINAS_ACTIVIDADES = {"actividades.html": 2, "en/activities.html": 3, "pt/atividades.html": 4}


def foto(photo, label, attrs):
    from hashlib import md5

    name = photo[0]
    digest = md5(name.encode(), usedforsecurity=False).hexdigest()
    folder = f"{digest[0]}/{digest[:2]}"
    if photo in ACTIVIDADES[:2]:
        url = f"{UPLOAD}thumb/{folder}/{name}/1280px-{name}"
    else:
        url = f"{UPLOAD}{folder}/{name}"
    return f'<img src="{url}" alt="{escape(label)}" {attrs}>'


def credito(photo, css=""):
    return f'<a {css}href="{COMMONS}{photo[0]}">{escape(photo[1])}</a>'


def portada_de_la_semana(hoy=None):
    """Foto de portada: rota entre las de data/portadas.json, una por semana."""
    import json
    from datetime import date
    from pathlib import Path

    fotos = [p for p in json.loads(Path("data/portadas.json").read_text(encoding="utf-8")) if p.get("activa")]
    anio, semana, _ = (hoy or date.today()).isocalendar()
    return fotos[(anio * 53 + semana) % len(fotos)]


def aplicar_visuales(path, html):
    if path in PORTADAS:
        start = '<section class="hero">'
        p = portada_de_la_semana()
        lang = {2: "es", 3: "en", 4: "pt"}[PORTADAS[path]]
        image = f'<img src="{p["imagen"]}" alt="{escape(p[lang])}" class="hero-foto" fetchpriority="high">'
        html = html.replace(start, '<section class="hero hero-fotografica">' + image, 1)
        enlace = f'<a class="hero-credito" href="{p["fuente"]}">{escape(p[lang])} · {escape(p["credito"])}</a>'
        html = html.replace('</section>', enlace + '</section>', 1)
    elif path in PAGINAS_ACTIVIDADES:
        label_index = PAGINAS_ACTIVIDADES[path]
        figures = []
        for photo in ACTIVIDADES:
            label = photo[label_index]
            image = foto(photo, label, 'loading="lazy" decoding="async"')
            figures.append(f'<figure>{image}<figcaption>{escape(label)}{credito(photo)}</figcaption></figure>')
        gallery = '<div class="container actividades-fotos">' + ''.join(figures) + '</div>'
        html = html.replace('</section>', '</section>' + gallery, 1)
    else:
        return html
    return html.replace('</head>', '<link rel="stylesheet" href="/css/portada-actividades.css">\n</head>', 1)
