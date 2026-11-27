"""Inserta el mapa de destinos en la portada y en la página de destinos (los tres idiomas)."""

PAGINAS = {"index.html": "es", "destinos.html": "es", "en/index.html": "en", "en/destinos.html": "en",
           "pt/index.html": "pt", "pt/destinos.html": "pt"}
TEXTOS = {
    "es": ("Mapa de destinos", "Ubicá cada destino y calculá distancias. Tocá un punto para ver su guía."),
    "en": ("Destinations map", "See where each destination is and how far apart they are. Tap a point to open its guide."),
    "pt": ("Mapa de destinos", "Veja onde fica cada destino e as distâncias entre eles. Toque em um ponto para abrir o guia."),
}


def agregar_mapa(path, html):
    if path not in PAGINAS or 'id="mapa-patagonia"' in html:
        return html
    titulo, subtitulo = TEXTOS[PAGINAS[path]]
    seccion = f"""<section class="section mapa-destinos">
    <div class="container">
      <h2 class="section-title" style="text-align:center">{titulo}</h2>
      <p class="section-subtitle">{subtitulo}</p>
      <div id="mapa-patagonia" role="region" aria-label="{titulo}"></div>
    </div>
  </section>

  """
    ancla = '<section class="section booking-cta">'
    if ancla not in html:
        return html
    html = html.replace(ancla, seccion + ancla, 1)
    html = html.replace("</head>", '<link rel="stylesheet" href="/js/vendor/leaflet/leaflet.css">\n'
                        '<link rel="stylesheet" href="/css/mapa.css">\n</head>', 1)
    return html.replace("</body>", '<script src="/js/vendor/leaflet/leaflet.js"></script>\n'
                        '<script src="/js/mapa-destinos.js" defer></script>\n</body>', 1)
