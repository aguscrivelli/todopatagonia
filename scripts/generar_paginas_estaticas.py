"""
TodoPatagonia.com — Generador de páginas estáticas con contenido dinámico
Genera:
  - actividades.html / en/activities.html / pt/atividades.html
  - como-llegar.html / en/how-to-get-there.html / pt/como-chegar.html

Se invoca desde el workflow generar-paginas-estaticas.yml cada 4 semanas,
y también puede correrse manualmente: python scripts/generar_paginas_estaticas.py
"""

import os
import json
from pathlib import Path
from datetime import datetime

import anthropic

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
BOOKING_AFFILIATE = "101940420"
GYG_AFFILIATE = "FCJ97KZ"

# ---------------------------------------------------------------------------
# Config de idiomas
# ---------------------------------------------------------------------------
IDIOMAS = {
    "es": {
        "lang": "es",
        "dir": Path("."),
        "font": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@400;500;600&display=swap",
        "css_prefix": "css/",
        "js_prefix": "js/",
        "logo_href": "/",
        "nav": [
            ("/destinos.html", "Destinos"),
            ("/actividades.html", "Actividades"),
            ("/como-llegar.html", "Cómo llegar"),
            ("/blog/", "Blog"),
        ],
        "lang_links": [
            ("/", "ES"),
            ("/en/", "EN"),
            ("/pt/", "PT"),
        ],
        "footer_destinos": [
            ("/destinos/el-calafate.html", "El Calafate"),
            ("/destinos/bariloche.html", "Bariloche"),
            ("/destinos/ushuaia.html", "Ushuaia"),
            ("/destinos/el-chalten.html", "El Chaltén"),
        ],
        "footer_links": [
            ("/blog/", "Blog"),
            ("/como-llegar.html", "Cómo llegar"),
            ("/privacidad.html", "Privacidad"),
            ("/afiliados.html", "Aviso de afiliados"),
        ],
        "footer_copy": "© 2024 TodoPatagonia.com · Sitio independiente de viajes · <a href='/afiliados.html'>Aviso de afiliados</a>",
        "prompt_lang": "Spanish (Argentina)",
        "booking_cta": "Reservá tu alojamiento en Patagonia",
        "booking_btn": "Buscar hoteles en Booking.com",
        "gyg_cta": "Reservá tus tours en Patagonia",
        "gyg_btn": "Ver actividades en GetYourGuide",
        "last_updated": "Última actualización",
    },
    "en": {
        "lang": "en",
        "dir": Path("en"),
        "font": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@400;500;600&display=swap",
        "css_prefix": "../css/",
        "js_prefix": "../js/",
        "logo_href": "/",
        "nav": [
            ("/en/destinos.html", "Destinations"),
            ("/en/activities.html", "Activities"),
            ("/en/how-to-get-there.html", "How to Get There"),
            ("/en/blog/", "Blog"),
        ],
        "lang_links": [
            ("/", "ES"),
            ("/en/", "EN"),
            ("/pt/", "PT"),
        ],
        "footer_destinos": [
            ("/en/destinos/el-calafate.html", "El Calafate"),
            ("/en/destinos/bariloche.html", "Bariloche"),
            ("/en/destinos/ushuaia.html", "Ushuaia"),
            ("/en/destinos/el-chalten.html", "El Chaltén"),
        ],
        "footer_links": [
            ("/en/blog/", "Blog"),
            ("/en/how-to-get-there.html", "How to Get There"),
            ("/en/privacy.html", "Privacy"),
            ("/en/affiliates.html", "Affiliate Disclosure"),
        ],
        "footer_copy": "© 2024 TodoPatagonia.com · Independent travel site · <a href='/en/affiliates.html'>Affiliate Disclosure</a>",
        "prompt_lang": "English",
        "booking_cta": "Find your Patagonia accommodation",
        "booking_btn": "Search hotels on Booking.com",
        "gyg_cta": "Book your Patagonia tours",
        "gyg_btn": "Browse activities on GetYourGuide",
        "last_updated": "Last updated",
    },
    "pt": {
        "lang": "pt",
        "dir": Path("pt"),
        "font": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@400;500;600&display=swap",
        "css_prefix": "../css/",
        "js_prefix": "../js/",
        "logo_href": "/",
        "nav": [
            ("/pt/destinos.html", "Destinos"),
            ("/pt/atividades.html", "Atividades"),
            ("/pt/como-chegar.html", "Como Chegar"),
            ("/pt/blog/", "Blog"),
        ],
        "lang_links": [
            ("/", "ES"),
            ("/en/", "EN"),
            ("/pt/", "PT"),
        ],
        "footer_destinos": [
            ("/pt/destinos/el-calafate.html", "El Calafate"),
            ("/pt/destinos/bariloche.html", "Bariloche"),
            ("/pt/destinos/ushuaia.html", "Ushuaia"),
            ("/pt/destinos/el-chalten.html", "El Chaltén"),
        ],
        "footer_links": [
            ("/pt/blog/", "Blog"),
            ("/pt/como-chegar.html", "Como Chegar"),
            ("/pt/privacidade.html", "Privacidade"),
            ("/pt/afiliados.html", "Aviso de Afiliados"),
        ],
        "footer_copy": "© 2024 TodoPatagonia.com · Site independente de viagens · <a href='/pt/afiliados.html'>Aviso de Afiliados</a>",
        "prompt_lang": "Brazilian Portuguese",
        "booking_cta": "Reserve sua acomodação na Patagônia",
        "booking_btn": "Buscar hotéis no Booking.com",
        "gyg_cta": "Reserve seus passeios na Patagônia",
        "gyg_btn": "Ver atividades no GetYourGuide",
        "last_updated": "Última atualização",
    },
}

# ---------------------------------------------------------------------------
# Páginas a generar: tipo -> config por idioma
# ---------------------------------------------------------------------------
PAGINAS = {
    "actividades": {
        "es": {"filename": "actividades.html", "title_key": "actividades"},
        "en": {"filename": "activities.html", "title_key": "activities"},
        "pt": {"filename": "atividades.html", "title_key": "atividades"},
    },
    "como_llegar": {
        "es": {"filename": "como-llegar.html", "title_key": "como_llegar"},
        "en": {"filename": "how-to-get-there.html", "title_key": "how_to_get_there"},
        "pt": {"filename": "como-chegar.html", "title_key": "como_chegar"},
    },
}


# ---------------------------------------------------------------------------
# Generación de contenido con Claude
# ---------------------------------------------------------------------------

def generar_contenido_actividades(idioma_cfg):
    """Llama a Claude para generar el contenido de la página de actividades."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    lang = idioma_cfg["prompt_lang"]

    prompt = f"""You are an expert travel writer specializing in Patagonia (Argentina and Chile).
Create comprehensive content for an ACTIVITIES page for TodoPatagonia.com, written in {lang}.

The page should cover the best activities and experiences in Patagonia, organized by category.
Make it inspiring, practical, and SEO-optimized.

Include:
- page_title (max 65 chars, SEO optimized, in {lang})
- meta_description (max 155 chars, in {lang})
- hero_title: main H1 heading (short, impactful)
- hero_subtitle: 1-2 sentences introducing Patagonia's activities
- categories: array of 6 activity categories, each with:
  - emoji: relevant emoji
  - name: category name
  - description: 2-3 sentences about this activity in Patagonia
  - top_spots: array of 2-3 specific places/parks where to do it
  - difficulty: "Fácil / Easy / Fácil", "Moderado / Moderate / Moderado", or "Difícil / Difficult / Difícil"
  - best_season: best time of year (1 sentence)
  - gyg_query: 2-3 word search term for GetYourGuide (in English always)
- seasonal_guide: object with 4 seasons (spring, summer, autumn, winter), each with:
  - name: season name in {lang}
  - months: months in {lang} (e.g. "Diciembre - Febrero")
  - highlight: 1 sentence about what's special
  - best_for: array of 2-3 activity names
- practical_tips: array of 4 tips for planning activities in Patagonia
- closing: inspiring 2-sentence closing paragraph

Respond ONLY with valid JSON. No markdown, no explanation.
{{
  "page_title": "...",
  "meta_description": "...",
  "hero_title": "...",
  "hero_subtitle": "...",
  "categories": [...],
  "seasonal_guide": {{
    "spring": {{"name": "...", "months": "...", "highlight": "...", "best_for": [...]}},
    "summer": {{"name": "...", "months": "...", "highlight": "...", "best_for": [...]}},
    "autumn": {{"name": "...", "months": "...", "highlight": "...", "best_for": [...]}},
    "winter": {{"name": "...", "months": "...", "highlight": "...", "best_for": [...]}}
  }},
  "practical_tips": [...],
  "closing": "..."
}}"""

    return solicitar_json(client, prompt)


def solicitar_json(client, prompt):
    for max_tokens in (6000, 9000):
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        if message.stop_reason == "max_tokens":
            error = ValueError("La respuesta de Claude quedó truncada")
            continue
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].removeprefix("json")
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError as exc:
            error = exc
    raise error


def generar_contenido_como_llegar(idioma_cfg):
    """Llama a Claude para generar el contenido de la página cómo llegar."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    lang = idioma_cfg["prompt_lang"]

    prompt = f"""You are an expert travel writer specializing in Patagonia (Argentina and Chile).
Create comprehensive content for a HOW TO GET THERE page for TodoPatagonia.com, written in {lang}.

This page helps travelers understand how to reach the main Patagonian destinations by air and land.
Make it practical, up-to-date, and SEO-optimized.

Include:
- page_title (max 65 chars, SEO optimized, in {lang})
- meta_description (max 155 chars, in {lang})
- hero_title: main H1 heading (short, impactful)
- hero_subtitle: 1-2 sentences about reaching Patagonia
- intro: 2-3 sentence introduction about the logistics of traveling to Patagonia
- destinations: array of 6 main destinations (Bariloche, El Calafate, Ushuaia, El Chaltén, Península Valdés, Torres del Paine), each with:
  - name: destination name
  - emoji: relevant emoji
  - nearest_airport: name and IATA code
  - from_buenos_aires: how to get there from Buenos Aires (flights + duration, buses, key info)
  - from_santiago: how to get there from Santiago Chile (if relevant)
  - local_transport: how to get around once there (1-2 sentences)
  - best_tip: one practical tip specific to this destination (1 sentence)
- transport_modes: array of 3 transport modes (airplane, bus, car/rental), each with:
  - mode: name in {lang}
  - emoji: emoji
  - pros: array of 2-3 advantages
  - cons: array of 1-2 disadvantages
  - tip: 1 practical tip
- border_crossings: array of 2-3 key Argentina-Chile border crossings with brief info
- booking_tips: array of 4 practical tips for booking transport to Patagonia

Respond ONLY with valid JSON. No markdown, no explanation.
{{
  "page_title": "...",
  "meta_description": "...",
  "hero_title": "...",
  "hero_subtitle": "...",
  "intro": "...",
  "destinations": [...],
  "transport_modes": [...],
  "border_crossings": [...],
  "booking_tips": [...]
}}"""

    return solicitar_json(client, prompt)


# ---------------------------------------------------------------------------
# Renderizado HTML
# ---------------------------------------------------------------------------

NAV_HTML = """  <header class="site-header">
    <div class="container">
      <div class="header-inner">
        <a href="{logo_href}" class="logo"><span class="logo-todo">Todo</span><span class="logo-patagonia">Patagonia</span></a>
        <nav class="main-nav">
{nav_links}
        </nav>
        <div class="lang-switcher">
{lang_links}
        </div>
      </div>
    </div>
  </header>"""

FOOTER_HTML = """  <footer class="site-footer">
    <div class="container">
      <div class="footer-inner">
        <div class="footer-brand">
          <a href="/" class="logo"><span class="logo-todo">Todo</span><span class="logo-patagonia">Patagonia</span></a>
          <p>Guía independiente de viajes a la Patagonia</p>
        </div>
        <div class="footer-links">
          <h4>Destinos</h4>
{footer_destinos}
        </div>
        <div class="footer-links">
          <h4>Explorar</h4>
{footer_links}
        </div>
        <div class="footer-links">
          <h4>Idioma</h4>
          <a href="/">Español</a>
          <a href="/en/">English</a>
          <a href="/pt/">Português</a>
        </div>
      </div>
      <div class="footer-bottom">
        <p>{footer_copy}</p>
      </div>
    </div>
  </footer>"""


def render_nav(cfg):
    nav_links = "\n".join(
        f'          <a href="{href}">{label}</a>' for href, label in cfg["nav"]
    )
    lang_links = "\n".join(
        f'          <a href="{href}">{label}</a>' for href, label in cfg["lang_links"]
    )
    return NAV_HTML.format(
        logo_href=cfg["logo_href"],
        nav_links=nav_links,
        lang_links=lang_links,
    )


def render_footer(cfg):
    footer_destinos = "\n".join(
        f'          <a href="{href}">{label}</a>' for href, label in cfg["footer_destinos"]
    )
    footer_links = "\n".join(
        f'          <a href="{href}">{label}</a>' for href, label in cfg["footer_links"]
    )
    return FOOTER_HTML.format(
        footer_destinos=footer_destinos,
        footer_links=footer_links,
        footer_copy=cfg["footer_copy"],
    )


def render_actividades_html(contenido, cfg):
    """Renderiza la página de actividades completa."""
    now = datetime.now().strftime("%B %Y")
    lang = cfg["lang"]

    # Hero
    hero = f"""  <section class="dest-hero" style="background:linear-gradient(135deg,#1a3a5c 0%,#2d5a3d 100%);color:#fff;padding:100px 0 60px">
    <div class="container" style="text-align:center">
      <h1 style="font-family:'Playfair Display',serif;font-size:clamp(2rem,5vw,3.5rem);margin-bottom:16px">{contenido['hero_title']}</h1>
      <p style="font-size:1.2rem;opacity:0.9;max-width:600px;margin:0 auto 24px">{contenido['hero_subtitle']}</p>
      <p style="font-size:0.85rem;opacity:0.6">{cfg['last_updated']}: {now}</p>
    </div>
  </section>"""

    # Categorías de actividades
    cats_html = ""
    for cat in contenido.get("categories", []):
        spots = "".join(f"<li>{s}</li>" for s in cat.get("top_spots", []))
        gyg_url = f"https://www.getyourguide.com/patagonia-l97178/?q={cat['gyg_query'].replace(' ', '+')}&partner_id={GYG_AFFILIATE}"
        cats_html += f"""
      <div style="background:#fff;border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,0.08);padding:28px;display:flex;flex-direction:column;gap:12px">
        <div style="font-size:2.5rem">{cat['emoji']}</div>
        <h3 style="font-family:'Playfair Display',serif;color:#1a3a5c;font-size:1.3rem;margin:0">{cat['name']}</h3>
        <p style="color:#6c757d;font-size:0.95rem;margin:0">{cat['description']}</p>
        <ul style="color:#2d6a9f;font-size:0.9rem;padding-left:18px;margin:0">{spots}</ul>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:4px">
          <span style="background:#e9ecef;border-radius:20px;padding:4px 12px;font-size:0.8rem;color:#495057">🗓 {cat['best_season']}</span>
          <span style="background:#e9ecef;border-radius:20px;padding:4px 12px;font-size:0.8rem;color:#495057">💪 {cat['difficulty']}</span>
        </div>
        <a href="{gyg_url}" target="_blank" rel="noopener sponsored"
           style="display:inline-block;background:#d4650a;color:#fff;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.9rem;text-align:center;margin-top:auto">
          Ver tours disponibles →
        </a>
      </div>"""

    # Guía estacional
    seasons_html = ""
    season_colors = {"spring": "#4a8c5c", "summer": "#d4650a", "autumn": "#8B4513", "winter": "#2d6a9f"}
    for season_key, color in season_colors.items():
        s = contenido.get("seasonal_guide", {}).get(season_key, {})
        if not s:
            continue
        best_for = " · ".join(s.get("best_for", []))
        seasons_html += f"""
      <div style="border-left:4px solid {color};padding:16px 20px;background:#f8f9fa;border-radius:0 8px 8px 0">
        <h4 style="color:{color};margin:0 0 4px;font-size:1.05rem">{s['name']} <span style="font-weight:400;color:#6c757d;font-size:0.9rem">· {s['months']}</span></h4>
        <p style="margin:4px 0;color:#495057;font-size:0.95rem">{s['highlight']}</p>
        <p style="margin:4px 0;color:#6c757d;font-size:0.85rem">🎯 {best_for}</p>
      </div>"""

    # Tips
    tips_html = "".join(
        f'<li style="margin-bottom:12px;padding-left:4px">{t}</li>'
        for t in contenido.get("practical_tips", [])
    )

    gyg_main = f"https://www.getyourguide.com/patagonia-l97178/?partner_id={GYG_AFFILIATE}"
    booking_main = f"https://www.booking.com/region/ar/patagonia.html?aid={BOOKING_AFFILIATE}"

    page = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{contenido['meta_description']}">
  <title>{contenido['page_title']} | TodoPatagonia.com</title>
  <link rel="stylesheet" href="{cfg['css_prefix']}style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{cfg['font']}" rel="stylesheet">
</head>
<body>

{render_nav(cfg)}

{hero}

  <!-- ACTIVIDADES GRID -->
  <section class="section">
    <div class="container">
      <h2 class="section-title" style="text-align:center;margin-bottom:12px">{contenido['hero_title']}</h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:24px;margin-top:40px">
{cats_html}
      </div>
    </div>
  </section>

  <!-- GUÍA ESTACIONAL -->
  <section class="section" style="background:#f8f9fa">
    <div class="container">
      <h2 class="section-title" style="text-align:center">¿Cuándo ir?</h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;margin-top:32px">
{seasons_html}
      </div>
    </div>
  </section>

  <!-- CTA GETYOURGUIDE -->
  <section class="section booking-cta">
    <div class="container">
      <div class="booking-box" style="background:linear-gradient(135deg,#2d5a3d,#4a8c5c)">
        <h2>{cfg['gyg_cta']}</h2>
        <p>Excursiones con guías expertos, cancelación gratis en la mayoría</p>
        <a href="{gyg_main}" target="_blank" rel="noopener sponsored" class="btn-booking" style="background:#d4650a">
          {cfg['gyg_btn']}
        </a>
      </div>
    </div>
  </section>

  <!-- TIPS PRÁCTICOS -->
  <section class="section">
    <div class="container" style="max-width:760px">
      <h2 class="section-title">💡 Consejos para planificar</h2>
      <ul style="margin-top:24px;list-style:none;padding:0">
        {tips_html}
      </ul>
      <p style="margin-top:32px;font-style:italic;color:#6c757d">{contenido['closing']}</p>
    </div>
  </section>

  <!-- CTA BOOKING -->
  <section class="section booking-cta" style="padding:40px 0">
    <div class="container">
      <div class="booking-box">
        <h2>{cfg['booking_cta']}</h2>
        <a href="{booking_main}" target="_blank" rel="noopener sponsored" class="btn-booking">
          {cfg['booking_btn']}
        </a>
      </div>
    </div>
  </section>

{render_footer(cfg)}

  <script src="{cfg['js_prefix']}main.js" defer></script>
</body>
</html>"""
    return page


def render_como_llegar_html(contenido, cfg):
    """Renderiza la página de cómo llegar completa."""
    now = datetime.now().strftime("%B %Y")
    lang = cfg["lang"]

    hero = f"""  <section class="dest-hero" style="background:linear-gradient(135deg,#2d6a9f 0%,#1a3a5c 100%);color:#fff;padding:100px 0 60px">
    <div class="container" style="text-align:center">
      <h1 style="font-family:'Playfair Display',serif;font-size:clamp(2rem,5vw,3.5rem);margin-bottom:16px">{contenido['hero_title']}</h1>
      <p style="font-size:1.2rem;opacity:0.9;max-width:600px;margin:0 auto 24px">{contenido['hero_subtitle']}</p>
      <p style="font-size:0.85rem;opacity:0.6">{cfg['last_updated']}: {now}</p>
    </div>
  </section>"""

    # Intro
    intro_html = f"""  <section class="section" style="padding:48px 0">
    <div class="container" style="max-width:760px">
      <p style="font-size:1.1rem;color:#495057;line-height:1.7">{contenido['intro']}</p>
    </div>
  </section>"""

    # Destinos
    destinos_html = ""
    for d in contenido.get("destinations", []):
        from_bsas = d.get("from_buenos_aires", "")
        from_scl = d.get("from_santiago", "")
        scl_block = f'<p style="margin:8px 0"><strong>🇨🇱 Desde Santiago:</strong> {from_scl}</p>' if from_scl else ""
        destinos_html += f"""
      <div style="background:#fff;border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,0.08);padding:28px;border-top:4px solid #2d6a9f">
        <h3 style="font-family:'Playfair Display',serif;color:#1a3a5c;font-size:1.25rem;margin:0 0 16px">{d['emoji']} {d['name']}</h3>
        <p style="margin:8px 0;color:#495057"><strong>✈️ Aeropuerto:</strong> {d['nearest_airport']}</p>
        <p style="margin:8px 0;color:#495057"><strong>🇦🇷 Desde Buenos Aires:</strong> {from_bsas}</p>
        {scl_block}
        <p style="margin:8px 0;color:#495057"><strong>🚌 Transporte local:</strong> {d['local_transport']}</p>
        <div style="background:#e8f4f8;border-radius:8px;padding:12px 16px;margin-top:12px">
          <p style="margin:0;color:#2d6a9f;font-size:0.9rem">💡 <em>{d['best_tip']}</em></p>
        </div>
      </div>"""

    # Modos de transporte
    transport_html = ""
    transport_colors = {"airplane": "#2d6a9f", "bus": "#2d5a3d", "car": "#8B4513"}
    for i, t in enumerate(contenido.get("transport_modes", [])):
        color = list(transport_colors.values())[i % 3]
        pros = "".join(f"<li style='color:#2d5a3d'>✓ {p}</li>" for p in t.get("pros", []))
        cons = "".join(f"<li style='color:#d4650a'>✗ {c}</li>" for c in t.get("cons", []))
        transport_html += f"""
      <div style="background:#fff;border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,0.08);padding:24px;border-left:4px solid {color}">
        <h3 style="color:{color};font-size:1.15rem;margin:0 0 12px">{t['emoji']} {t['mode']}</h3>
        <ul style="list-style:none;padding:0;margin:0 0 12px">{pros}{cons}</ul>
        <p style="color:#6c757d;font-size:0.9rem;margin:0;font-style:italic">💡 {t['tip']}</p>
      </div>"""

    # Pasos fronterizos
    borders_html = ""
    for b in contenido.get("border_crossings", []):
        borders_html += f'<li style="margin-bottom:12px;padding-left:4px"><strong>{b}</strong></li>' if isinstance(b, str) else f'<li style="margin-bottom:12px"><strong>{b.get("name","")}</strong> — {b.get("info","")}</li>'

    # Booking tips
    tips_html = "".join(
        f'<li style="margin-bottom:12px;padding-left:4px">{t}</li>'
        for t in contenido.get("booking_tips", [])
    )

    booking_main = f"https://www.booking.com/region/ar/patagonia.html?aid={BOOKING_AFFILIATE}"

    page = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{contenido['meta_description']}">
  <title>{contenido['page_title']} | TodoPatagonia.com</title>
  <link rel="stylesheet" href="{cfg['css_prefix']}style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{cfg['font']}" rel="stylesheet">
</head>
<body>

{render_nav(cfg)}

{hero}

{intro_html}

  <!-- DESTINOS: CÓMO LLEGAR -->
  <section class="section" style="background:#f8f9fa">
    <div class="container">
      <h2 class="section-title" style="text-align:center;margin-bottom:40px">Por destino</h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:24px">
{destinos_html}
      </div>
    </div>
  </section>

  <!-- MODOS DE TRANSPORTE -->
  <section class="section">
    <div class="container">
      <h2 class="section-title" style="text-align:center;margin-bottom:40px">¿Cómo moverse?</h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px">
{transport_html}
      </div>
    </div>
  </section>

  <!-- CTA BOOKING -->
  <section class="section booking-cta" style="padding:48px 0">
    <div class="container">
      <div class="booking-box">
        <h2>{cfg['booking_cta']}</h2>
        <p>Incluye hoteles, cabañas, hostels y más en toda la Patagonia</p>
        <a href="{booking_main}" target="_blank" rel="noopener sponsored" class="btn-booking">
          {cfg['booking_btn']}
        </a>
      </div>
    </div>
  </section>

  <!-- PASOS FRONTERIZOS + TIPS -->
  <section class="section" style="background:#f8f9fa">
    <div class="container" style="max-width:760px">
      <h2 class="section-title">🛂 Pasos fronterizos Argentina-Chile</h2>
      <ul style="margin-top:24px;list-style:none;padding:0">
        {borders_html}
      </ul>
      <h2 class="section-title" style="margin-top:48px">💡 Tips para reservar</h2>
      <ul style="margin-top:24px;list-style:none;padding:0">
        {tips_html}
      </ul>
    </div>
  </section>

{render_footer(cfg)}

  <script src="{cfg['js_prefix']}main.js" defer></script>
</body>
</html>"""
    return page


# ---------------------------------------------------------------------------
# Páginas legales estáticas
# ---------------------------------------------------------------------------

def render_legal_html(lang, tipo, cfg):
    """Genera páginas legales (privacidad, afiliados) para EN y PT."""
    if tipo == "privacy":
        if lang == "en":
            title = "Privacy Policy | TodoPatagonia.com"
            h1 = "Privacy Policy"
            body = """<p>TodoPatagonia.com takes your privacy seriously. This policy explains how we handle your information.</p>
      <h2>Information We Collect</h2>
      <p>We do not collect personal data directly. Our site uses Google Analytics to understand traffic patterns (anonymized) and affiliate links from Booking.com and GetYourGuide.</p>
      <h2>Cookies</h2>
      <p>We use cookies from Google Analytics and affiliate partners to track link performance. These do not identify you personally.</p>
      <h2>Affiliate Links</h2>
      <p>Some links on this site are affiliate links. We receive a small commission if you make a purchase through them, at no extra cost to you. See our <a href="/en/affiliates.html">Affiliate Disclosure</a>.</p>
      <h2>Contact</h2>
      <p>Questions? Email us at info@todopatagonia.com</p>"""
        else:  # pt
            title = "Política de Privacidade | TodoPatagonia.com"
            h1 = "Política de Privacidade"
            body = """<p>O TodoPatagonia.com leva sua privacidade a sério. Esta política explica como tratamos suas informações.</p>
      <h2>Informações que Coletamos</h2>
      <p>Não coletamos dados pessoais diretamente. Usamos o Google Analytics para entender padrões de tráfego (anonimizados) e links de afiliados do Booking.com e GetYourGuide.</p>
      <h2>Cookies</h2>
      <p>Usamos cookies do Google Analytics e parceiros afiliados para acompanhar o desempenho dos links. Eles não identificam você pessoalmente.</p>
      <h2>Links de Afiliados</h2>
      <p>Alguns links neste site são links de afiliados. Recebemos uma pequena comissão se você fizer uma compra por meio deles, sem custo extra para você. Veja nosso <a href="/pt/afiliados.html">Aviso de Afiliados</a>.</p>
      <h2>Contato</h2>
      <p>Dúvidas? Envie um email para info@todopatagonia.com</p>"""

    else:  # affiliates / afiliados
        if lang == "en":
            title = "Affiliate Disclosure | TodoPatagonia.com"
            h1 = "Affiliate Disclosure"
            body = """<p>TodoPatagonia.com participates in affiliate programs with the following platforms:</p>
      <ul>
        <li><strong>Booking.com Partner Program:</strong> If you book accommodation through our links, we receive a small commission from Booking.com. The price you pay is exactly the same.</li>
        <li><strong>GetYourGuide Partner Program:</strong> If you purchase tours or activities through our links, we receive a commission. No additional cost to you.</li>
        <li><strong>Google AdSense:</strong> We display Google ads on some pages of the site.</li>
      </ul>
      <p>These commissions allow us to keep the site free and continue publishing useful content about Patagonia. We only recommend services we trust. The opinions expressed on this site are independent and not influenced by affiliate agreements.</p>"""
        else:  # pt
            title = "Aviso de Afiliados | TodoPatagonia.com"
            h1 = "Aviso de Afiliados"
            body = """<p>O TodoPatagonia.com participa de programas de afiliados com as seguintes plataformas:</p>
      <ul>
        <li><strong>Programa de Parceiros Booking.com:</strong> Se você reservar acomodação através dos nossos links, recebemos uma pequena comissão do Booking.com. O preço que você paga é exatamente o mesmo.</li>
        <li><strong>Programa de Parceiros GetYourGuide:</strong> Se você comprar passeios ou atividades através dos nossos links, recebemos uma comissão. Sem custo adicional para você.</li>
        <li><strong>Google AdSense:</strong> Exibimos anúncios do Google em algumas páginas do site.</li>
      </ul>
      <p>Essas comissões nos permitem manter o site gratuito e continuar publicando conteúdo útil sobre a Patagônia. Recomendamos apenas serviços em que confiamos. As opiniões expressas neste site são independentes e não são influenciadas por acordos de afiliados.</p>"""

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="{cfg['css_prefix']}style.css">
  <link href="{cfg['font']}" rel="stylesheet">
</head>
<body>
{render_nav(cfg)}
  <main style="padding:60px 0 80px">
    <div class="container" style="max-width:760px">
      <h1 style="font-family:'Playfair Display',serif;color:#1a3a5c;margin-bottom:24px">{h1}</h1>
      {body}
    </div>
  </main>
{render_footer(cfg)}
</body>
</html>"""


def render_blog_index(lang, cfg):
    """Genera un index de blog vacío compatible con el JS (oculta la sección si no hay artículos)."""
    titles = {"es": "Blog", "en": "Blog", "pt": "Blog"}
    descs = {
        "es": "Guías, itinerarios y consejos para viajar a la Patagonia.",
        "en": "Guides, itineraries and tips for traveling to Patagonia.",
        "pt": "Guias, roteiros e dicas para viajar à Patagônia.",
    }
    blog_json = {
        "es": "/blog/articles.json",
        "en": "/en/blog/articles.json",
        "pt": "/pt/blog/articles.json",
    }
    blog_base = {
        "es": "/blog/",
        "en": "/en/blog/",
        "pt": "/pt/blog/",
    }

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{descs[lang]}">
  <title>{titles[lang]} | TodoPatagonia.com</title>
  <link rel="stylesheet" href="{cfg['css_prefix']}style.css">
  <link href="{cfg['font']}" rel="stylesheet">
  <script>
    const BLOG_JSON = '{blog_json[lang]}';
    const BLOG_BASE = '{blog_base[lang]}';
  </script>
</head>
<body>
{render_nav(cfg)}
  <section class="section">
    <div class="container">
      <h1 class="section-title" style="text-align:center">{titles[lang]}</h1>
      <p class="section-sub" style="text-align:center">{descs[lang]}</p>
      <div class="cards-grid" id="blog-grid" style="margin-top:40px"></div>
    </div>
  </section>
{render_footer(cfg)}
  <script src="{cfg['js_prefix']}main.js" defer></script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("🤖 TodoPatagonia — Generador de páginas estáticas")
    print("=" * 50)

    if not ANTHROPIC_API_KEY:
        raise SystemExit("Falta ANTHROPIC_API_KEY")

    for idioma_key, cfg in IDIOMAS.items():
        cfg["dir"].mkdir(parents=True, exist_ok=True)

        # --- Actividades ---
        filename = PAGINAS["actividades"][idioma_key]["filename"]
        filepath = cfg["dir"] / filename
        print(f"\n🎯 Generando actividades [{idioma_key.upper()}]...")
        try:
            contenido = generar_contenido_actividades(cfg)
            html = render_actividades_html(contenido, cfg)
            filepath.write_text(html, encoding="utf-8")
            print(f"   ✅ {filepath}")
        except Exception as e:
            raise RuntimeError(f"No se pudo generar {idioma_key}: {e}") from e

        # --- Cómo llegar ---
        filename2 = PAGINAS["como_llegar"][idioma_key]["filename"]
        filepath2 = cfg["dir"] / filename2
        print(f"\n✈️  Generando cómo llegar [{idioma_key.upper()}]...")
        try:
            contenido2 = generar_contenido_como_llegar(cfg)
            html2 = render_como_llegar_html(contenido2, cfg)
            filepath2.write_text(html2, encoding="utf-8")
            print(f"   ✅ {filepath2}")
        except Exception as e:
            raise RuntimeError(f"No se pudo generar {idioma_key}: {e}") from e

    # --- Páginas legales EN ---
    print("\n📋 Generando páginas legales EN...")
    Path("en").mkdir(exist_ok=True)
    cfg_en = IDIOMAS["en"]
    (Path("en") / "privacy.html").write_text(render_legal_html("en", "privacy", cfg_en), encoding="utf-8")
    (Path("en") / "affiliates.html").write_text(render_legal_html("en", "affiliates", cfg_en), encoding="utf-8")
    print("   ✅ en/privacy.html + en/affiliates.html")

    # --- Páginas legales PT ---
    print("\n📋 Generando páginas legales PT...")
    Path("pt").mkdir(exist_ok=True)
    cfg_pt = IDIOMAS["pt"]
    (Path("pt") / "privacidade.html").write_text(render_legal_html("pt", "privacy", cfg_pt), encoding="utf-8")
    (Path("pt") / "afiliados.html").write_text(render_legal_html("pt", "affiliates", cfg_pt), encoding="utf-8")
    print("   ✅ pt/privacidade.html + pt/afiliados.html")

    # --- Blogs EN/PT ---
    print("\n📝 Generando index de blogs EN/PT...")
    (Path("en") / "blog").mkdir(exist_ok=True)
    (Path("pt") / "blog").mkdir(exist_ok=True)
    (Path("en") / "blog" / "index.html").write_text(render_blog_index("en", cfg_en), encoding="utf-8")
    (Path("pt") / "blog" / "index.html").write_text(render_blog_index("pt", cfg_pt), encoding="utf-8")
    print("   ✅ en/blog/index.html + pt/blog/index.html")

    print("\n🎉 ¡Listo! Todas las páginas generadas.")


if __name__ == "__main__":
    main()
