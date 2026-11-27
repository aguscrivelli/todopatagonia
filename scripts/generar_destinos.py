"""
TodoPatagonia.com — Generador de páginas de destinos
Genera destinos/bariloche.html, destinos/el-calafate.html, etc.
en ES, EN y PT. Se ejecuta una sola vez (o cuando se quiera regenerar).
"""

import os
import json
import re
import urllib.request
import urllib.parse
import random
from pathlib import Path
from datetime import datetime

import anthropic
from slugify import slugify

BOOKING_AFFILIATE = "101940420"
GYG_AFFILIATE = "FCJ97KZ"
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

DESTINOS_INFO = [
    {
        "nombre": "Bariloche",
        "slug": "bariloche",
        "emoji": "🏔️",
        "unsplash_query": "Bariloche lake mountains Argentina Nahuel Huapi",
        "booking_query": "Bariloche",
        "gyg_query": "Bariloche",
    },
    {
        "nombre": "El Calafate",
        "slug": "el-calafate",
        "emoji": "🧊",
        "unsplash_query": "El Calafate Perito Moreno glacier Patagonia",
        "booking_query": "El Calafate",
        "gyg_query": "El Calafate glacier",
    },
    {
        "nombre": "Ushuaia",
        "slug": "ushuaia",
        "emoji": "🐧",
        "unsplash_query": "Ushuaia Tierra del Fuego Argentina end of the world",
        "booking_query": "Ushuaia",
        "gyg_query": "Ushuaia",
    },
    {
        "nombre": "El Chaltén",
        "slug": "el-chalten",
        "emoji": "⛰️",
        "unsplash_query": "Fitz Roy El Chalten trekking Patagonia",
        "booking_query": "El Chaltén",
        "gyg_query": "El Chalten Fitz Roy",
    },
    {
        "nombre": "Península Valdés",
        "slug": "peninsula-valdes",
        "emoji": "🐋",
        "unsplash_query": "Peninsula Valdes whale watching Patagonia Argentina",
        "booking_query": "Península Valdés",
        "gyg_query": "Peninsula Valdes",
    },
    {
        "nombre": "Torres del Paine",
        "slug": "torres-del-paine",
        "emoji": "🗻",
        "unsplash_query": "Torres del Paine national park Chile trekking",
        "booking_query": "Torres del Paine",
        "gyg_query": "Torres del Paine",
    },
]

IDIOMAS = {
    "es": {
        "lang": "es",
        "dir": "destinos",
        "css_prefix": "../",
        "nav_prefix": "/",
        "prompt_instruction": "Escribí en español rioplatense (Argentina). Usá 'vos' en lugar de 'tú'.",
        "prompt_lang": "español",
        "cta_booking": "Encontrá tu alojamiento en {dest}",
        "cta_booking_sub": "Los mejores hoteles y cabañas al mejor precio",
        "cta_booking_btn": "Ver hoteles en Booking.com",
        "cta_tours": "Tours y excursiones en {dest}",
        "cta_tours_btn": "Ver tours en GetYourGuide",
        "footer_legal": "© 2024 TodoPatagonia.com · <a href='/afiliados.html'>Aviso de afiliados</a> · <a href='/privacidad.html'>Privacidad</a>",
        "nav": {"destinos": "Destinos", "actividades": "Actividades", "como_llegar": "Cómo llegar", "blog": "Blog"},
        "section_highlights": "Por qué visitar",
        "section_activities": "Qué hacer",
        "section_howto": "Cómo llegar",
        "section_tips": "Consejos prácticos",
        "section_hotels": "Dónde alojarse",
        "last_updated": "Última actualización",
    },
    "en": {
        "lang": "en",
        "dir": "en/destinos",
        "css_prefix": "../../",
        "nav_prefix": "/en/",
        "prompt_instruction": "Write in fluent, natural English for international travelers.",
        "prompt_lang": "English",
        "cta_booking": "Find your accommodation in {dest}",
        "cta_booking_sub": "Best hotels and lodges at the best price",
        "cta_booking_btn": "View hotels on Booking.com",
        "cta_tours": "Tours & activities in {dest}",
        "cta_tours_btn": "View tours on GetYourGuide",
        "footer_legal": "© 2024 TodoPatagonia.com · <a href='/en/affiliates.html'>Affiliate Disclosure</a> · <a href='/en/privacy.html'>Privacy</a>",
        "nav": {"destinos": "Destinations", "actividades": "Activities", "como_llegar": "How to Get There", "blog": "Blog"},
        "section_highlights": "Why Visit",
        "section_activities": "What to Do",
        "section_howto": "How to Get There",
        "section_tips": "Practical Tips",
        "section_hotels": "Where to Stay",
        "last_updated": "Last updated",
    },
    "pt": {
        "lang": "pt",
        "dir": "pt/destinos",
        "css_prefix": "../../",
        "nav_prefix": "/pt/",
        "prompt_instruction": "Escreva em português brasileiro natural e fluente.",
        "prompt_lang": "português brasileiro",
        "cta_booking": "Encontre sua acomodação em {dest}",
        "cta_booking_sub": "Os melhores hotéis e pousadas pelo melhor preço",
        "cta_booking_btn": "Ver hotéis no Booking.com",
        "cta_tours": "Tours e atividades em {dest}",
        "cta_tours_btn": "Ver tours no GetYourGuide",
        "footer_legal": "© 2024 TodoPatagonia.com · <a href='/pt/afiliados.html'>Aviso de afiliados</a> · <a href='/pt/privacidade.html'>Privacidade</a>",
        "nav": {"destinos": "Destinos", "actividades": "Atividades", "como_llegar": "Como Chegar", "blog": "Blog"},
        "section_highlights": "Por que visitar",
        "section_activities": "O que fazer",
        "section_howto": "Como chegar",
        "section_tips": "Dicas práticas",
        "section_hotels": "Onde se hospedar",
        "last_updated": "Última atualização",
    },
}


def buscar_foto_unsplash(query):
    if not UNSPLASH_ACCESS_KEY:
        return None
    try:
        params = urllib.parse.urlencode({
            "query": query,
            "orientation": "landscape",
            "per_page": 5,
            "content_filter": "high",
        })
        url = f"https://api.unsplash.com/search/photos?{params}"
        req = urllib.request.Request(url, headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        results = data.get("results", [])
        if not results:
            return None
        foto = random.choice(results[:3])
        return {
            "url": foto["urls"]["regular"],
            "url_small": foto["urls"]["small"],
            "alt": foto.get("alt_description") or query,
            "author_name": foto["user"]["name"],
            "author_url": foto["user"]["links"]["html"],
            "unsplash_url": foto["links"]["html"],
        }
    except Exception as e:
        print(f"⚠️  Unsplash error: {e}")
        return None


def generar_contenido_destino(destino_info, idioma_cfg):
    """Llama a Claude para generar el contenido de la página de destino."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    nombre = destino_info["nombre"]
    lang = idioma_cfg["prompt_lang"]
    instruction = idioma_cfg["prompt_instruction"]

    prompt = f"""You are an expert travel writer specializing in Patagonia (Argentina and Chile).
Create comprehensive destination page content for "{nombre}" in {lang}.
{instruction}

The page must include:
- A compelling page title (max 65 chars, SEO optimized)
- Meta description (max 155 chars)
- A short hero subtitle (1 sentence, evocative)
- Section: Why Visit {nombre} (3-4 bullet points with emoji, each with a short title and 1-2 sentence description)
- Section: What to Do (5-6 top activities/attractions, each with a title and 2-3 sentences)
- Section: How to Get There (practical transport info: flights, buses, distances)
- Section: Where to Stay (3 categories: budget, mid-range, luxury — brief description each)
- Section: Practical Tips (best time to visit, weather, currency, what to pack — 4-5 tips)
- Closing paragraph (2-3 sentences, inspiring call to action)

Respond ONLY with valid JSON:
{{
  "title": "...",
  "meta_description": "...",
  "hero_subtitle": "...",
  "why_visit": [
    {{"emoji": "🏔️", "title": "...", "text": "..."}}
  ],
  "activities": [
    {{"title": "...", "text": "..."}}
  ],
  "how_to_get_there": "... (HTML paragraph or short paragraphs)",
  "where_to_stay": {{
    "budget": "...",
    "midrange": "...",
    "luxury": "..."
  }},
  "practical_tips": [
    {{"emoji": "📅", "title": "...", "text": "..."}}
  ],
  "closing": "..."
}}"""

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if not json_match:
        raise ValueError(f"No JSON en respuesta de Claude para {nombre} [{idioma_cfg['lang']}]")
    return json.loads(json_match.group())


def render_destino_html(destino_info, contenido, idioma_cfg, foto):
    """Renderiza la página HTML completa del destino."""
    lang = idioma_cfg["lang"]
    cfg = idioma_cfg
    slug = destino_info["slug"]
    nombre = destino_info["nombre"]
    css_prefix = cfg["css_prefix"]
    nav = cfg["nav"]
    nav_prefix = cfg["nav_prefix"]
    now = datetime.now()

    # Hreflang URLs
    url_es = f"https://todopatagonia.com/destinos/{slug}.html"
    url_en = f"https://todopatagonia.com/en/destinos/{slug}.html"
    url_pt = f"https://todopatagonia.com/pt/destinos/{slug}.html"

    # Active lang
    active = {"es": "", "en": "", "pt": ""}
    active[lang] = ' class="active"'

    # Fecha
    meses_es = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
    meses_pt = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    if lang == "es":
        fecha = f"{now.day} de {meses_es[now.month-1]} de {now.year}"
    elif lang == "pt":
        fecha = f"{now.day} de {meses_pt[now.month-1]} de {now.year}"
    else:
        fecha = now.strftime("%B %d, %Y")

    # Foto hero
    if foto:
        hero_img = f"""<figure class="dest-hero-image">
      <img src="{foto['url']}" srcset="{foto['url_small']} 400w, {foto['url']} 1080w"
           sizes="(max-width:600px) 400px, 1080px" alt="{foto['alt']}" loading="eager">
      <figcaption>Foto de <a href="{foto['author_url']}?utm_source=todopatagonia&utm_medium=referral" target="_blank" rel="noopener">{foto['author_name']}</a> en <a href="{foto['unsplash_url']}?utm_source=todopatagonia&utm_medium=referral" target="_blank" rel="noopener">Unsplash</a></figcaption>
    </figure>"""
        og_image = f'<meta property="og:image" content="{foto["url"]}">'
    else:
        hero_img = ""
        og_image = ""

    # Why visit bullets
    why_html = "\n".join([
        f'<div class="highlight-item"><span class="highlight-emoji">{h["emoji"]}</span><div><strong>{h["title"]}</strong><p>{h["text"]}</p></div></div>'
        for h in contenido.get("why_visit", [])
    ])

    # Activities
    activities_html = "\n".join([
        f'<div class="activity-item"><h3>{a["title"]}</h3><p>{a["text"]}</p></div>'
        for a in contenido.get("activities", [])
    ])

    # Practical tips
    tips_html = "\n".join([
        f'<div class="tip-item"><span class="tip-emoji">{t["emoji"]}</span><div><strong>{t["title"]}</strong><p>{t["text"]}</p></div></div>'
        for t in contenido.get("practical_tips", [])
    ])

    # Where to stay
    ws = contenido.get("where_to_stay", {})
    budget_label = {"es": "Económico", "en": "Budget", "pt": "Econômico"}[lang]
    mid_label = {"es": "Intermedio", "en": "Mid-range", "pt": "Intermediário"}[lang]
    lux_label = {"es": "Premium", "en": "Luxury", "pt": "Premium"}[lang]
    stay_html = f"""<div class="stay-grid">
      <div class="stay-card"><h4>💰 {budget_label}</h4><p>{ws.get("budget","")}</p></div>
      <div class="stay-card"><h4>🏨 {mid_label}</h4><p>{ws.get("midrange","")}</p></div>
      <div class="stay-card"><h4>⭐ {lux_label}</h4><p>{ws.get("luxury","")}</p></div>
    </div>"""

    booking_dest = urllib.parse.quote(nombre)
    gyg_dest = urllib.parse.quote(destino_info["gyg_query"])

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{contenido['meta_description']}">
  <meta property="og:title" content="{contenido['title']}">
  <meta property="og:description" content="{contenido['meta_description']}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://todopatagonia.com/{cfg['dir']}/{slug}.html">
  {og_image}
  <link rel="canonical" href="https://todopatagonia.com/{cfg['dir']}/{slug}.html">
  <link rel="alternate" hreflang="es" href="{url_es}">
  <link rel="alternate" hreflang="en" href="{url_en}">
  <link rel="alternate" hreflang="pt" href="{url_pt}">
  <link rel="alternate" hreflang="x-default" href="{url_es}">
  <title>{contenido['title']} | TodoPatagonia.com</title>
  <link rel="stylesheet" href="{css_prefix}css/style.css">
  <link rel="stylesheet" href="{css_prefix}css/destino.css">
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
          <a href="{url_es}"{active['es']}>ES</a>
          <a href="{url_en}"{active['en']}>EN</a>
          <a href="{url_pt}"{active['pt']}>PT</a>
        </div>
      </div>
    </div>
  </header>

  <section class="dest-hero">
    <div class="dest-hero-overlay"></div>
    <div class="container dest-hero-content">
      <span class="dest-emoji">{destino_info['emoji']}</span>
      <h1>{contenido['title']}</h1>
      <p class="dest-subtitle">{contenido['hero_subtitle']}</p>
    </div>
  </section>

  <main class="dest-main">
    <div class="container">

      {hero_img}

      <section class="dest-section dest-why">
        <h2>{cfg['section_highlights']}</h2>
        <div class="highlights-grid">
          {why_html}
        </div>
      </section>

      <div class="dest-booking-cta">
        <h3>{cfg['cta_booking'].replace('{dest}', nombre)}</h3>
        <p>{cfg['cta_booking_sub']}</p>
        <a href="https://www.booking.com/searchresults.html?ss={booking_dest}&aid={BOOKING_AFFILIATE}"
           target="_blank" rel="noopener sponsored" class="btn-booking">
          {cfg['cta_booking_btn']}
        </a>
      </div>

      <section class="dest-section dest-activities">
        <h2>{cfg['section_activities']}</h2>
        <div class="activities-grid">
          {activities_html}
        </div>
      </section>

      <div class="dest-tours-cta">
        <h3>{cfg['cta_tours'].replace('{dest}', nombre)}</h3>
        <a href="https://www.getyourguide.com/s/?q={gyg_dest}&partner_id={GYG_AFFILIATE}"
           target="_blank" rel="noopener sponsored" class="btn-primary">
          {cfg['cta_tours_btn']}
        </a>
      </div>

      <section class="dest-section dest-howto">
        <h2>{cfg['section_howto']}</h2>
        <div class="howto-content">
          {contenido.get('how_to_get_there', '')}
        </div>
      </section>

      <section class="dest-section dest-stay">
        <h2>{cfg['section_hotels']}</h2>
        {stay_html}
        <div style="margin-top:1.5rem;text-align:center;">
          <a href="https://www.booking.com/searchresults.html?ss={booking_dest}&aid={BOOKING_AFFILIATE}"
             target="_blank" rel="noopener sponsored" class="btn-booking">
            {cfg['cta_booking_btn']}
          </a>
        </div>
      </section>

      <section class="dest-section dest-tips">
        <h2>{cfg['section_tips']}</h2>
        <div class="tips-grid">
          {tips_html}
        </div>
      </section>

      <div class="dest-closing">
        <p>{contenido.get('closing','')}</p>
      </div>

      <p class="dest-updated"><small>{cfg['last_updated']}: {fecha}</small></p>

    </div>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-bottom">
        <p>{cfg['footer_legal']}</p>
      </div>
    </div>
  </footer>
</body>
</html>"""


def main():
    print("🗺️  Generador de páginas de destinos — TodoPatagonia.com")
    print("=" * 55)

    for destino in DESTINOS_INFO:
        print(f"\n📍 {destino['nombre']}")

        # Buscar foto UNA vez, compartir entre idiomas
        print("   📸 Buscando foto Unsplash...")
        foto = buscar_foto_unsplash(destino["unsplash_query"])
        if foto:
            print(f"   → {foto['author_name']}")
        else:
            print("   → Sin foto")

        for idioma_key, idioma_cfg in IDIOMAS.items():
            dest_dir = Path(idioma_cfg["dir"])
            dest_file = dest_dir / f"{destino['slug']}.html"

            print(f"   🌐 Generando [{idioma_key.upper()}]...", end=" ", flush=True)
            try:
                contenido = generar_contenido_destino(destino, idioma_cfg)
                html = render_destino_html(destino, contenido, idioma_cfg, foto)
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file.write_text(html, encoding="utf-8")
                print(f"✅ {dest_file}")
            except Exception as e:
                print(f"❌ Error: {e}")

    print("\n🎉 ¡Destinos generados en ES, EN y PT!")


if __name__ == "__main__":
    main()
