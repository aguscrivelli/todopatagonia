"""
TodoPatagonia.com — Generador automático de artículos con Claude AI
Se ejecuta desde GitHub Actions cada semana.
"""

import os
import json
import random
import re
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

BOOKING_AFFILIATE = "TUAFILIADO"  # Reemplazar con tu ID de Booking
GYG_AFFILIATE = "TUPARTNER"       # Reemplazar con tu ID de GetYourGuide

TEMPLATE_ARTICULO_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{meta_description}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{meta_description}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="https://todopatagonia.com/blog/{slug}.html">
  <link rel="canonical" href="https://todopatagonia.com/blog/{slug}.html">
  <title>{title} | TodoPatagonia.com</title>
  <link rel="stylesheet" href="../css/style.css">
  <link rel="stylesheet" href="../css/article.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
</head>
<body>
  <header class="site-header">
    <div class="container">
      <div class="header-inner">
        <a href="/" class="logo"><span class="logo-todo">Todo</span><span class="logo-patagonia">Patagonia</span></a>
        <nav class="main-nav">
          <a href="/destinos.html">Destinos</a>
          <a href="/actividades.html">Actividades</a>
          <a href="/como-llegar.html">Cómo llegar</a>
          <a href="/blog/">Blog</a>
        </nav>
        <div class="lang-switcher">
          <a href="/blog/{slug}.html" class="active">ES</a>
          <a href="/en/blog/{slug}.html">EN</a>
          <a href="/pt/blog/{slug}.html">PT</a>
        </div>
      </div>
    </div>
  </header>

  <main class="article-main">
    <div class="container">
      <article class="article-content">
        <div class="article-header">
          <span class="article-category">{category}</span>
          <h1>{title}</h1>
          <p class="article-excerpt">{excerpt}</p>
          <div class="article-meta">
            <span>📅 {date}</span>
            <span>📍 {destination}</span>
            <span>⏱️ {read_time} min de lectura</span>
          </div>
        </div>

        <div class="article-body">
          {body_html}
        </div>

        <div class="article-booking-cta">
          <h3>¿Listo para ir a {destination}?</h3>
          <p>Encontrá los mejores alojamientos al mejor precio</p>
          <a href="https://www.booking.com/searchresults.html?ss={destination_encoded}&aid={booking_affiliate}"
             target="_blank" rel="noopener sponsored" class="btn-booking">
            Ver hoteles en Booking.com
          </a>
        </div>

        <div class="article-tours-cta">
          <h3>Tours y excursiones en {destination}</h3>
          <a href="https://www.getyourguide.com/s/?q={destination_encoded}&partner_id={gyg_affiliate}"
             target="_blank" rel="noopener sponsored" class="btn-primary">
            Ver tours en GetYourGuide
          </a>
        </div>

      </article>
    </div>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-bottom">
        <p>© 2024 TodoPatagonia.com · <a href="/afiliados.html">Aviso de afiliados</a> · <a href="/privacidad.html">Privacidad</a></p>
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


def generar_articulo_claude(destino, categoria):
    """Llama a la API de Claude para generar el artículo."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""Sos un experto en turismo en la Patagonia argentina y chilena.
Escribí un artículo SEO completo sobre "{destino['nombre']}" con enfoque en "{categoria}".

El artículo debe:
- Tener un título atractivo y optimizado para SEO (máx 65 caracteres)
- Una descripción meta (máx 155 caracteres)
- Un excerpt/resumen de 2 oraciones
- El cuerpo del artículo en HTML semántico (sin <html>, <head>, <body>)
- Usar encabezados H2 y H3 para estructura
- Incluir información práctica: precios aproximados en USD, cómo llegar, mejor época para visitar
- Mínimo 800 palabras
- Tono amigable pero informativo
- Incluir una sección "Consejos prácticos" al final

Respondé SOLO con un JSON válido con esta estructura exacta:
{{
  "title": "...",
  "meta_description": "...",
  "excerpt": "...",
  "category": "{categoria}",
  "read_time": 5,
  "body_html": "... (HTML completo del cuerpo) ..."
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    # Extraer JSON de la respuesta
    text = message.content[0].text
    # Buscar el JSON en la respuesta
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if not json_match:
        raise ValueError("No se encontró JSON en la respuesta de Claude")

    return json.loads(json_match.group())


def guardar_articulo(destino, articulo_data):
    """Genera el HTML del artículo y actualiza articles.json."""
    slug = slugify(articulo_data["title"], allow_unicode=False, separator="-")
    fecha = datetime.now().strftime("%Y-%m-%d")
    fecha_display = datetime.now().strftime("%-d de %B de %Y")

    # Generar HTML
    html = TEMPLATE_ARTICULO_HTML.format(
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
    )

    # Guardar archivo HTML
    blog_path = Path("blog")
    blog_path.mkdir(exist_ok=True)
    (blog_path / f"{slug}.html").write_text(html, encoding="utf-8")
    print(f"✅ Artículo guardado: blog/{slug}.html")

    # Actualizar articles.json
    articles_path = blog_path / "articles.json"
    articles = json.loads(articles_path.read_text(encoding="utf-8")) if articles_path.exists() else []

    # Verificar que no existe ya
    if any(a["slug"] == slug for a in articles):
        print(f"⚠️  El artículo {slug} ya existe en articles.json, saltando.")
        return slug

    articles.insert(0, {
        "slug": slug,
        "title": articulo_data["title"],
        "excerpt": articulo_data["excerpt"],
        "category": articulo_data["category"],
        "emoji": destino["emoji"],
        "date": fecha,
        "destination": destino["nombre"],
    })

    articles_path.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ articles.json actualizado ({len(articles)} artículos)")

    return slug


def main():
    print("🤖 Generador de contenido TodoPatagonia.com")
    print("=" * 50)

    destino = elegir_destino()
    categoria = random.choice(CATEGORIAS)

    print(f"📍 Destino: {destino['nombre']}")
    print(f"📂 Categoría: {categoria}")
    print("🔄 Generando con Claude...")

    articulo = generar_articulo_claude(destino, categoria)
    slug = guardar_articulo(destino, articulo)

    print(f"🎉 Listo! → blog/{slug}.html")


if __name__ == "__main__":
    main()
