"""
TodoPatagonia.com — Generador automático de artículos con Claude AI
Se ejecuta desde GitHub Actions cada semana.
"""

import os
import json
import random
import re
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

import anthropic
from slugify import slugify

# ============================================================
# CONFIGURACIÓN
# ============================================================

DESTINOS = [
    {"nombre": "El Calafate", "emoji": "🧊"},
    {"nombre": "Bariloche", "emoji": "🏔️"},
    {"nombre": "Ushuaia", "emoji": "🐧"},
    {"nombre": "El Chaltén", "emoji": "⛰️"},
    {"nombre": "Península Valdés", "emoji": "🐋"},
    {"nombre": "Torres del Paine", "emoji": "🗻"},
    {"nombre": "San Martín de los Andes", "emoji": "🌲"},
    {"nombre": "Neuquén", "emoji": "🦕"},
    {"nombre": "Comodoro Rivadavia", "emoji": "🛢️"},
    {"nombre": "Puerto Madryn", "emoji": "🌊"},
]

CATEGORIAS = [
    "Guía de viaje",
    "Trekking",
    "Glaciares",
    "Fauna",
    "Gastronomía",
    "Alojamiento",
    "Consejos prácticos",
    "Temporadas",
]

BOOKING_AFFILIATE = "101940420"  # Booking.com via Commission Junction
GYG_AFFILIATE = "FCJ97KZ"         # GetYourGuide Partner ID
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

# Configuración multiidioma
IDIOMAS = {
    "es": {
        "lang": "es",
        "blog_dir": "blog",
        "base_url": "https://todopatagonia.com",
        "nav": {"destinos": "Destinos", "actividades": "Actividades", "como_llegar": "Cómo llegar", "blog": "Blog"},
        "cta_booking": "¿Listo para ir a {dest}?",
        "cta_booking_sub": "Encontrá los mejores alojamientos al mejor precio",
        "cta_booking_btn": "Ver hoteles en Booking.com",
        "cta_tours": "Tours y excursiones en {dest}",
        "cta_tours_btn": "Ver tours en GetYourGuide",
        "read_time_label": "min de lectura",
        "footer_legal": "© 2024 TodoPatagonia.com · <a href='/afiliados.html'>Aviso de afiliados</a> · <a href='/privacidad.html'>Privacidad</a>",
        "prompt_lang": "español",
        "prompt_instruction": "Escribí en español rioplatense (Argentina). Usá 'vos' en lugar de 'tú'.",
    },
    "en": {
        "lang": "en",
        "blog_dir": "en/blog",
        "base_url": "https://todopatagonia.com/en",
        "nav": {"destinos": "Destinations", "actividades": "Activities", "como_llegar": "How to Get There", "blog": "Blog"},
        "cta_booking": "Ready to visit {dest}?",
        "cta_booking_sub": "Find the best accommodations at the best price",
        "cta_booking_btn": "View hotels on Booking.com",
        "cta_tours": "Tours & activities in {dest}",
        "cta_tours_btn": "View tours on GetYourGuide",
        "read_time_label": "min read",
        "footer_legal": "© 2024 TodoPatagonia.com · <a href='/en/affiliates.html'>Affiliate Disclosure</a> · <a href='/en/privacy.html'>Privacy</a>",
        "prompt_lang": "English",
        "prompt_instruction": "Write in fluent, natural English for international travelers.",
    },
    "pt": {
        "lang": "pt",
        "blog_dir": "pt/blog",
        "base_url": "https://todopatagonia.com/pt",
        "nav": {"destinos": "Destinos", "actividades": "Atividades", "como_llegar": "Como Chegar", "blog": "Blog"},
        "cta_booking": "Pronto para ir a {dest}?",
        "cta_booking_sub": "Encontre as melhores acomodações pelo melhor preço",
        "cta_booking_btn": "Ver hotéis no Booking.com",
        "cta_tours": "Tours e atividades em {dest}",
        "cta_tours_btn": "Ver tours no GetYourGuide",
        "read_time_label": "min de leitura",
        "footer_legal": "© 2024 TodoPatagonia.com · <a href='/pt/afiliados.html'>Aviso de afiliados</a> · <a href='/pt/privacidade.html'>Privacidade</a>",
        "prompt_lang": "português brasileiro",
        "prompt_instruction": "Escreva em português brasileiro natural e fluente.",
    },
}

def get_template_articulo(idioma_cfg, slug, css_prefix="../"):
    """Genera el template HTML del artículo según el idioma."""
    lang = idioma_cfg["lang"]
    nav = idioma_cfg["nav"]
    base_url = idioma_cfg["base_url"]

    # Rutas de navegación según idioma
    if lang == "es":
        nav_prefix = "/"
        alt_es = f"/blog/{slug}.html"
        alt_en = f"/en/blog/{slug}.html"
        alt_pt = f"/pt/blog/{slug}.html"
        active_es = ' class="active"'
        active_en = ''
        active_pt = ''
    elif lang == "en":
        nav_prefix = "/en/"
        alt_es = f"/blog/{slug}.html"
        alt_en = f"/en/blog/{slug}.html"
        alt_pt = f"/pt/blog/{slug}.html"
        active_es = ''
        active_en = ' class="active"'
        active_pt = ''
    else:  # pt
        nav_prefix = "/pt/"
        alt_es = f"/blog/{slug}.html"
        alt_en = f"/en/blog/{slug}.html"
        alt_pt = f"/pt/blog/{slug}.html"
        active_es = ''
        active_en = ''
        active_pt = ' class="active"'

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{{meta_description}}">
  <meta property="og:title" content="{{title}}">
  <meta property="og:description" content="{{meta_description}}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{base_url}/blog/{{slug}}.html">
  {{og_image_tag}}
  <link rel="canonical" href="{base_url}/blog/{{slug}}.html">
  <link rel="alternate" hreflang="es" href="https://todopatagonia.com{alt_es}">
  <link rel="alternate" hreflang="en" href="https://todopatagonia.com{alt_en}">
  <link rel="alternate" hreflang="pt" href="https://todopatagonia.com{alt_pt}">
  <title>{{title}} | TodoPatagonia.com</title>
  <link rel="stylesheet" href="{css_prefix}css/style.css">
  <link rel="stylesheet" href="{css_prefix}css/article.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
</head>
<body>
  <header class="site-header">
    <div class="container">
      <div class="header-inner">
        <a href="/" class="logo"><span class="logo-todo">Todo</span><span class="logo-patagonia">Patagonia</span></a>
        <nav class="main-nav">
          <a href="{nav_prefix}destinos.html">{nav['destinos']}</a>
          <a href="{nav_prefix}{ {"es": "actividades.html", "en": "activities.html", "pt": "atividades.html"}[lang] }">{nav['actividades']}</a>
          <a href="{nav_prefix}{ {"es": "como-llegar.html", "en": "how-to-get-there.html", "pt": "como-chegar.html"}[lang] }">{nav['como_llegar']}</a>
          <a href="{nav_prefix}blog/">{nav['blog']}</a>
        </nav>
        <div class="lang-switcher">
          <a href="{alt_es}"{active_es}>ES</a>
          <a href="{alt_en}"{active_en}>EN</a>
          <a href="{alt_pt}"{active_pt}>PT</a>
        </div>
      </div>
    </div>
  </header>

  <main class="article-main">
    <div class="container">
      <article class="article-content">
        <div class="article-header">
          <span class="article-category">{{category}}</span>
          <h1>{{title}}</h1>
          <p class="article-excerpt">{{excerpt}}</p>
          <div class="article-meta">
            <span>📅 {{date}}</span>
            <span>📍 {{destination}}</span>
            <span>⏱️ {{read_time}} {idioma_cfg['read_time_label']}</span>
          </div>
          {{hero_image_html}}
        </div>

        <div class="article-body">
          {{body_html}}
        </div>

        <div class="article-booking-cta">
          <h3>{idioma_cfg['cta_booking'].replace('{dest}', '{{destination}}')}</h3>
          <p>{idioma_cfg['cta_booking_sub']}</p>
          <a href="https://www.booking.com/searchresults.html?ss={{destination_encoded}}&aid={{booking_affiliate}}"
             target="_blank" rel="noopener sponsored" class="btn-booking">
            {idioma_cfg['cta_booking_btn']}
          </a>
        </div>

        <div class="article-tours-cta">
          <h3>{idioma_cfg['cta_tours'].replace('{dest}', '{{destination}}')}</h3>
          <a href="https://www.getyourguide.com/s/?q={{destination_encoded}}&partner_id={{gyg_affiliate}}"
             target="_blank" rel="noopener sponsored" class="btn-primary">
            {idioma_cfg['cta_tours_btn']}
          </a>
        </div>

      </article>
    </div>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-bottom">
        <p>{idioma_cfg['footer_legal']}</p>
      </div>
    </div>
  </footer>
</body>
</html>"""


def elegir_destino():
    """Elige un destino: por input manual, o aleatorio evitando repetir el último."""
    destino_input = os.environ.get("DESTINO_INPUT", "").strip()

    if destino_input:
        # Buscar el destino en la lista
        for d in DESTINOS:
            if destino_input.lower() in d["nombre"].lower():
                return d

    # Cargar historial para no repetir
    history_path = Path("scripts/history.json")
    history = json.loads(history_path.read_text()) if history_path.exists() else []

    ultimos = set(history[-3:]) if history else set()
    disponibles = [d for d in DESTINOS if d["nombre"] not in ultimos]
    if not disponibles:
        disponibles = DESTINOS

    elegido = random.choice(disponibles)

    # Guardar en historial
    history.append(elegido["nombre"])
    history_path.write_text(json.dumps(history[-20:], ensure_ascii=False, indent=2))

    return elegido


def generar_articulo_claude(destino, categoria, idioma="es"):
    """Llama a la API de Claude para generar el artículo en el idioma dado."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    idioma_cfg = IDIOMAS[idioma]

    prompt = f"""You are an expert in tourism in Argentine and Chilean Patagonia.
Write a complete SEO article about "{destino['nombre']}" focusing on "{categoria}".
{idioma_cfg['prompt_instruction']}

The article must:
- Have an attractive SEO-optimized title (max 65 characters)
- A meta description (max 155 characters)
- An excerpt/summary of 2 sentences
- The article body in semantic HTML (without <html>, <head>, <body> tags)
- Use H2 and H3 headings for structure
- Include practical information: approximate prices in USD, how to get there, best time to visit
- Minimum 800 words
- Friendly but informative tone
- Include a "Practical Tips" section at the end

Respond ONLY with valid JSON with this exact structure:
{{
  "title": "...",
  "meta_description": "...",
  "excerpt": "...",
  "category": "{categoria}",
  "read_time": 5,
  "body_html": "... (full HTML body) ..."
}}"""

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    # Extraer JSON de la respuesta
    text = message.content[0].text
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if not json_match:
        raise ValueError("No se encontró JSON en la respuesta de Claude")

    return json.loads(json_match.group())


def buscar_foto_unsplash(query, orientation="landscape"):
    """Busca una foto en Unsplash y devuelve URL + crédito. Si falla, retorna None."""
    if not UNSPLASH_ACCESS_KEY:
        return None

    try:
        params = urllib.parse.urlencode({
            "query": query,
            "orientation": orientation,
            "per_page": 5,
            "content_filter": "high",
        })
        url = f"https://api.unsplash.com/search/photos?{params}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        results = data.get("results", [])
        if not results:
            return None

        # Elegir aleatoriamente entre los primeros 3 resultados
        foto = random.choice(results[:3])
        return {
            "url": foto["urls"]["regular"],        # ~1080px ancho
            "url_small": foto["urls"]["small"],    # ~400px para mobile
            "alt": foto.get("alt_description") or query,
            "author_name": foto["user"]["name"],
            "author_url": foto["user"]["links"]["html"],
            "unsplash_url": foto["links"]["html"],
        }
    except Exception as e:
        print(f"⚠️  Unsplash error: {e}")
        return None


def construir_hero_html(foto):
    """Construye el HTML del hero con foto Unsplash y crédito obligatorio."""
    if not foto:
        return ""
    return f"""<figure class="article-hero-image">
          <img src="{foto['url']}"
               srcset="{foto['url_small']} 400w, {foto['url']} 1080w"
               sizes="(max-width: 600px) 400px, 1080px"
               alt="{foto['alt']}" loading="eager">
          <figcaption>Foto de <a href="{foto['author_url']}?utm_source=todopatagonia&utm_medium=referral" target="_blank" rel="noopener">{foto['author_name']}</a> en <a href="{foto['unsplash_url']}?utm_source=todopatagonia&utm_medium=referral" target="_blank" rel="noopener">Unsplash</a></figcaption>
        </figure>"""


def guardar_articulo(destino, articulo_data, idioma="es", foto=None, slug=None):
    """Genera el HTML del artículo y actualiza articles.json para el idioma dado."""
    idioma_cfg = IDIOMAS[idioma]
    # Las tres versiones comparten el slug del artículo en español, así el
    # selector de idioma y los hreflang apuntan a páginas que existen.
    slug = slug or slugify(articulo_data["title"], allow_unicode=False, separator="-")
    fecha = datetime.now().strftime("%Y-%m-%d")

    # Formato de fecha según idioma
    meses_es = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
    meses_pt = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    now = datetime.now()
    if idioma == "es":
        fecha_display = f"{now.day} de {meses_es[now.month-1]} de {now.year}"
    elif idioma == "pt":
        fecha_display = f"{now.day} de {meses_pt[now.month-1]} de {now.year}"
    else:
        fecha_display = now.strftime("%B %d, %Y")

    # Foto: si no viene, buscarla (solo una vez por artículo, en ES la busca el main)
    if foto is None:
        query_foto = f"Patagonia {destino['nombre']} travel landscape"
        foto = buscar_foto_unsplash(query_foto)
        if foto:
            print(f"📸 Foto Unsplash [{idioma}]: {foto['author_name']}")
        else:
            print(f"📸 Sin foto Unsplash [{idioma}]")

    hero_image_html = construir_hero_html(foto)
    og_image_tag = f'<meta property="og:image" content="{foto["url"]}">' if foto else ""

    # Determinar prefijo CSS según profundidad del blog_dir
    blog_dir = idioma_cfg["blog_dir"]
    depth = len(Path(blog_dir).parts)
    css_prefix = "../" * depth

    # Generar template y HTML
    template = get_template_articulo(idioma_cfg, slug, css_prefix)
    html = template.format(
        slug=slug,
        title=articulo_data["title"],
        meta_description=articulo_data["meta_description"],
        excerpt=articulo_data["excerpt"],
        category=articulo_data["category"],
        date=fecha_display,
        destination=destino["nombre"],
        destination_encoded=destino["nombre"].replace(" ", "+"),
        read_time=articulo_data.get("read_time", 5),
        body_html=articulo_data["body_html"],
        booking_affiliate=BOOKING_AFFILIATE,
        gyg_affiliate=GYG_AFFILIATE,
        hero_image_html=hero_image_html,
        og_image_tag=og_image_tag,
    )

    # Guardar archivo HTML
    blog_path = Path(blog_dir)
    blog_path.mkdir(parents=True, exist_ok=True)
    (blog_path / f"{slug}.html").write_text(html, encoding="utf-8")
    print(f"✅ Artículo guardado: {blog_dir}/{slug}.html")

    # Actualizar articles.json del idioma
    articles_path = blog_path / "articles.json"
    articles = json.loads(articles_path.read_text(encoding="utf-8")) if articles_path.exists() else []

    if any(a["slug"] == slug for a in articles):
        print(f"⚠️  El artículo {slug} ya existe en {blog_dir}/articles.json, saltando.")
        return slug

    entry = {
        "slug": slug,
        "title": articulo_data["title"],
        "excerpt": articulo_data["excerpt"],
        "category": articulo_data["category"],
        "emoji": destino["emoji"],
        "date": fecha,
        "destination": destino["nombre"],
        "lang": idioma,
    }
    if foto:
        entry["image_url"] = foto["url_small"]
        entry["image_author"] = foto["author_name"]

    articles.insert(0, entry)
    articles_path.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ {blog_dir}/articles.json actualizado ({len(articles)} artículos)")

    return slug


DESTINOS_HOMEPAGE = {
    "El Calafate":               "El Calafate glacier Patagonia Argentina",
    "Bariloche":                 "Bariloche lake mountains Argentina",
    "Ushuaia":                   "Ushuaia Tierra del Fuego Argentina",
    "El Chaltén Fitz Roy":       "Fitz Roy mountain El Chalten Patagonia",
    "Península Valdés whales Patagonia": "Peninsula Valdes whale Patagonia",
    "Torres del Paine Chile":    "Torres del Paine Chile national park",
}


def actualizar_fotos_destinos():
    """Genera/actualiza data/destination-photos.json con fotos Unsplash para las cards del homepage."""
    if not UNSPLASH_ACCESS_KEY:
        print("⚠️  Sin UNSPLASH_ACCESS_KEY, no se actualizan fotos de destinos.")
        return

    data_path = Path("data")
    data_path.mkdir(exist_ok=True)
    photos_path = data_path / "destination-photos.json"

    # Cargar existente para no sobreescribir si la API falla parcialmente
    existing = {}
    if photos_path.exists():
        try:
            existing = json.loads(photos_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    updated = dict(existing)
    for dest_key, query in DESTINOS_HOMEPAGE.items():
        foto = buscar_foto_unsplash(query, orientation="landscape")
        if foto:
            updated[dest_key] = {
                "url": foto["url"],
                "url_small": foto["url_small"],
                "alt": foto["alt"],
                "author_name": foto["author_name"],
                "author_url": foto["author_url"],
            }
            print(f"📸 Foto para '{dest_key}': {foto['author_name']}")
        else:
            print(f"⚠️  Sin foto para '{dest_key}'")

    photos_path.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ destination-photos.json actualizado ({len(updated)} destinos)")


DESTINOS_JSON = Path("data/destinos.json")

CARD_TEMPLATE_ES = """
        <article class="dest-card" data-dest="{nombre}" data-href="/destinos/{slug}.html">
          <div class="dest-img">
            <div class="dest-placeholder">{emoji}</div>
          </div>
          <div class="dest-body">
            <h3>{nombre}</h3>
            <p>{descripcion}</p>
            <a href="/destinos/{slug}.html" class="card-link">Ver guía →</a>
          </div>
        </article>"""

CARD_TEMPLATE_EN = """
        <article class="dest-card" data-dest="{nombre}" data-href="/en/destinos/{slug}.html">
          <div class="dest-img">
            <div class="dest-placeholder">{emoji}</div>
          </div>
          <div class="dest-body">
            <h3>{nombre}</h3>
            <p>{descripcion}</p>
            <a href="/en/destinos/{slug}.html" class="card-link">See guide →</a>
          </div>
        </article>"""

CARD_TEMPLATE_PT = """
        <article class="dest-card" data-dest="{nombre}" data-href="/pt/destinos/{slug}.html">
          <div class="dest-img">
            <div class="dest-placeholder">{emoji}</div>
          </div>
          <div class="dest-body">
            <h3>{nombre}</h3>
            <p>{descripcion}</p>
            <a href="/pt/destinos/{slug}.html" class="card-link">Ver guia →</a>
          </div>
        </article>"""


def debe_agregar_destino():
    """Chequea si pasaron suficientes semanas desde la última incorporación."""
    if not DESTINOS_JSON.exists():
        return False
    data = json.loads(DESTINOS_JSON.read_text(encoding="utf-8"))
    if not data.get("pendientes"):
        print("ℹ️  No hay destinos pendientes para incorporar.")
        return False
    ultima = datetime.strptime(data["config"]["ultima_incorporacion"], "%Y-%m-%d")
    semanas = data["config"].get("semanas_entre_destinos", 4)
    dias_transcurridos = (datetime.now() - ultima).days
    if dias_transcurridos >= semanas * 7:
        print(f"🗓️  Han pasado {dias_transcurridos} días desde el último destino → incorporando nuevo.")
        return True
    print(f"ℹ️  Solo {dias_transcurridos} días desde el último destino (mínimo {semanas*7}). Sin cambios.")
    return False


def incorporar_nuevo_destino():
    """
    Toma el primer destino pendiente, genera sus páginas en ES/EN/PT,
    actualiza la home (index.html, en/index.html, pt/index.html)
    y actualiza data/destinos.json.
    """
    data = json.loads(DESTINOS_JSON.read_text(encoding="utf-8"))
    nuevo = data["pendientes"].pop(0)
    print(f"\n🆕 Incorporando nuevo destino: {nuevo['nombre']}")

    # Importar y usar el generador de destinos
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from generar_destinos import (
        generar_contenido_destino, render_destino_html,
        buscar_foto_unsplash as buscar_foto_dest, IDIOMAS as IDIOMAS_DEST
    )

    # Preparar info del destino en el formato esperado
    destino_info = {
        "nombre": nuevo["nombre"],
        "slug": nuevo["slug"],
        "emoji": nuevo["emoji"],
        "unsplash_query": nuevo.get("unsplash_query", f"{nuevo['nombre']} Patagonia Argentina"),
        "gyg_query": nuevo.get("gyg_query", nuevo["nombre"]),
    }

    # Buscar foto una vez
    foto = buscar_foto_dest(destino_info["unsplash_query"])

    # Generar página en los 3 idiomas
    for idioma_key, idioma_cfg in IDIOMAS_DEST.items():
        dest_dir = Path(idioma_cfg["dir"])
        dest_file = dest_dir / f"{nuevo['slug']}.html"
        try:
            contenido = generar_contenido_destino(destino_info, idioma_cfg)
            html = render_destino_html(destino_info, contenido, idioma_cfg, foto)
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file.write_text(html, encoding="utf-8")
            print(f"   ✅ {dest_file}")
        except Exception as e:
            print(f"   ❌ Error en [{idioma_key}]: {e}")

    # Agregar card a las 3 homes
    _agregar_card_a_home(nuevo)

    # Actualizar destinos.json
    nuevo["fecha_agregado"] = datetime.now().strftime("%Y-%m-%d")
    data["activos"].append(nuevo)
    data["config"]["ultima_incorporacion"] = datetime.now().strftime("%Y-%m-%d")
    DESTINOS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   ✅ data/destinos.json actualizado ({len(data['activos'])} activos, {len(data['pendientes'])} pendientes)")


def _agregar_card_a_home(destino):
    """Inserta la card del nuevo destino en index.html, en/index.html y pt/index.html."""
    configs = [
        ("index.html",    CARD_TEMPLATE_ES, "descripcion_es"),
        ("en/index.html", CARD_TEMPLATE_EN, "descripcion_en"),
        ("pt/index.html", CARD_TEMPLATE_PT, "descripcion_pt"),
    ]
    for filepath, template, desc_key in configs:
        path = Path(filepath)
        if not path.exists():
            print(f"   ⚠️  No encontré {filepath}, saltando.")
            continue
        html = path.read_text(encoding="utf-8")
        # Insertar antes del cierre del div de cards
        marker = "      </div>\n    </div>\n  </section>"
        if marker not in html:
            print(f"   ⚠️  No encontré marker en {filepath}, saltando.")
            continue
        card = template.format(
            nombre=destino["nombre"],
            slug=destino["slug"],
            emoji=destino["emoji"],
            descripcion=destino.get(desc_key, ""),
        )
        html = html.replace(marker, card + "\n" + marker, 1)
        path.write_text(html, encoding="utf-8")
        print(f"   ✅ Card agregada a {filepath}")


def main():
    print("🤖 Generador de contenido TodoPatagonia.com")
    print("=" * 50)

    # 1. Chequear si hay que incorporar un destino nuevo
    if debe_agregar_destino():
        incorporar_nuevo_destino()

    # 2. Generar artículo de blog
    destino = elegir_destino()
    categoria = random.choice(CATEGORIAS)

    print(f"\n📍 Destino del artículo: {destino['nombre']}")
    print(f"📂 Categoría: {categoria}")

    # Buscar foto UNA sola vez para los 3 idiomas
    query_foto = f"Patagonia {destino['nombre']} travel landscape"
    print("📸 Buscando foto Unsplash...")
    foto = buscar_foto_unsplash(query_foto)
    if foto:
        print(f"   → {foto['author_name']}: {foto['url'][:60]}...")
    else:
        print("   → Sin foto (se omite imagen hero)")

    publicadas = {}
    slug_es = None
    # Generar artículo en los 3 idiomas (EN y PT reutilizan el slug en español)
    for idioma in ["es", "en", "pt"]:
        print(f"\n🌐 Generando artículo en {idioma.upper()}...")
        articulo = generar_articulo_claude(destino, categoria, idioma)
        slug = guardar_articulo(destino, articulo, idioma, foto, slug=slug_es)
        slug_es = slug_es or slug
        publicadas[idioma] = f"{IDIOMAS[idioma]['blog_dir']}/{slug}.html"
        print(f"   → {publicadas[idioma]}")

    Path(os.environ.get("RUNNER_TEMP", "."), "guias-publicadas.json").write_text(
        json.dumps(publicadas), encoding="utf-8"
    )

    # 3. Actualizar fotos de destinos del homepage
    print("\n🖼️  Actualizando fotos de destinos...")
    actualizar_fotos_destinos()

    print("\n🎉 ¡Listo! Contenido generado en ES, EN y PT.")


if __name__ == "__main__":
    main()
