"""SEO técnico del sitio publicado (corre dentro de preparar_publicacion.py).

- Agrega canonical, hreflang y meta description donde falten.
- Agrega datos estructurados (JSON-LD) a los artículos del blog y a la portada.
- Genera sitemap.xml (con las versiones de cada idioma) y robots.txt.
"""
import json
import re
from datetime import date
from html import escape, unescape
from pathlib import Path

SITIO = "https://todopatagonia.com"
# Nombre de cada página fija en cada idioma (la clave es el nombre en español).
EQUIVALENTES = {
    "actividades.html": {"en": "activities.html", "pt": "atividades.html"},
    "como-llegar.html": {"en": "how-to-get-there.html", "pt": "como-chegar.html"},
    "privacidad.html": {"en": "privacy.html", "pt": "privacidade.html"},
    "afiliados.html": {"en": "affiliates.html", "pt": "afiliados.html"},
    "contacto.html": {"en": "contact.html", "pt": "contato.html"},
}
CONTACTO = {
    "/privacidad.html": ("/contacto.html", "Contacto"),
    "/en/privacy.html": ("/en/contact.html", "Contact"),
    "/pt/privacidade.html": ("/pt/contato.html", "Contato"),
}


def link_contacto(html):
    """Suma el link a la página de contacto al lado del de privacidad en el pie."""
    for priv, (destino, texto) in CONTACTO.items():
        if destino in html:
            continue
        for q in ("'", '"'):
            ancla = re.search(rf"<a href={q}{re.escape(priv)}{q}>[^<]*</a>", html)
            if ancla:
                link = f"<a href={q}{destino}{q}>{texto}</a>"
                fin = ancla.end()
                if html[fin:fin + 1] == "\n":
                    # Lista vertical (un link por renglón): va en su propio renglón, sin separador.
                    inicio_linea = html.rfind("\n", 0, ancla.start()) + 1
                    sangria = html[inicio_linea:ancla.start()]
                    return html[:fin] + "\n" + sangria + link + html[fin:]
                return html[:fin] + " · " + link + html[fin:]
    return html
DESCRIPCIONES = {
    "es": "TodoPatagonia: guías de viaje para la Patagonia argentina y chilena.",
    "en": "TodoPatagonia: travel guides to Argentine and Chilean Patagonia.",
    "pt": "TodoPatagonia: guias de viagem para a Patagônia argentina e chilena.",
}
EXCLUIR = ("ig.html", "ig/", "google")
# Verificación de Google Search Console (va en la portada).
GSC = '<meta name="google-site-verification" content="5TKB8u_pCKPpnMqXJNifmhv5zk_yJ3HHZf1ut4_BH18" />'


def idioma_y_clave(ruta):
    """'en/activities.html' -> ('en', 'actividades.html')."""
    lang = ruta.split("/", 1)[0] if ruta.startswith(("en/", "pt/")) else "es"
    resto = ruta[3:] if lang != "es" else ruta
    for es, otros in EQUIVALENTES.items():
        if otros.get(lang) == resto and lang != "es":
            return lang, es
    return lang, resto


def ruta_en(lang, clave):
    nombre = EQUIVALENTES.get(clave, {}).get(lang, clave) if lang != "es" else clave
    return nombre if lang == "es" else f"{lang}/{nombre}"


def url(ruta):
    return f"{SITIO}/{ruta[:-len('index.html')] if ruta.endswith('index.html') else ruta}"


def json_ld(datos):
    return '<script type="application/ld+json">' + json.dumps(datos, ensure_ascii=False) + "</script>"


def meta(html, nombre, atributo="name"):
    m = re.search(rf'<meta {atributo}="{nombre}" content="([^"]*)"', html)
    return unescape(m.group(1)) if m else ""


def procesar(salida):
    paginas = sorted(
        p.relative_to(salida).as_posix() for p in salida.rglob("*.html")
        if not p.relative_to(salida).as_posix().startswith(EXCLUIR)
    )
    existentes = set(paginas)
    grupos = {}
    for ruta in paginas:
        lang, clave = idioma_y_clave(ruta)
        grupos.setdefault(clave, {})[lang] = ruta

    for ruta in paginas:
        archivo = salida / ruta
        html = archivo.read_text(encoding="utf-8")
        if 'name="robots" content="noindex' in html:
            continue
        lang, clave = idioma_y_clave(ruta)
        con_link = link_contacto(html)
        if con_link != html:
            html = con_link
            archivo.write_text(html, encoding="utf-8")
        extra = []
        if ruta == "index.html" and "google-site-verification" not in html:
            extra.append(GSC)
        if 'rel="canonical"' not in html:
            extra.append(f'<link rel="canonical" href="{url(ruta)}">')
        if "hreflang" not in html and len(grupos[clave]) > 1:
            for l, r in sorted(grupos[clave].items()):
                extra.append(f'<link rel="alternate" hreflang="{l}" href="{url(r)}">')
            if "es" in grupos[clave]:
                extra.append(f'<link rel="alternate" hreflang="x-default" href="{url(grupos[clave]["es"])}">')
        if 'name="description"' not in html:
            extra.append(f'<meta name="description" content="{escape(DESCRIPCIONES[lang])}">')
        if "application/ld+json" not in html:
            titulo = unescape(re.search(r"<title>(.*?)</title>", html, re.S).group(1).split(" | ")[0].strip()) \
                if "<title>" in html else "TodoPatagonia"
            es_articulo = re.match(r"(en/|pt/)?blog/[^/]+\.html$", ruta) and not ruta.endswith("index.html")
            if es_articulo:
                datos = {
                    "@context": "https://schema.org", "@type": "Article", "headline": titulo,
                    "description": meta(html, "description"), "inLanguage": lang,
                    "mainEntityOfPage": url(ruta),
                    "publisher": {"@type": "Organization", "name": "TodoPatagonia", "url": SITIO},
                }
                imagen = meta(html, "og:image", "property")
                if imagen:
                    datos["image"] = imagen
                extra.append(json_ld(datos))
            elif clave == "index.html":
                extra.append(json_ld({
                    "@context": "https://schema.org", "@type": "WebSite", "name": "TodoPatagonia",
                    "url": url(ruta), "inLanguage": lang,
                }))
        if extra:
            html = html.replace("</head>", "  " + "\n  ".join(extra) + "\n</head>", 1)
            archivo.write_text(html, encoding="utf-8")

    # sitemap.xml con alternativas por idioma
    hoy = date.today().isoformat()
    entradas = []
    for ruta in paginas:
        html = (salida / ruta).read_text(encoding="utf-8")
        if 'name="robots" content="noindex' in html:
            continue
        lang, clave = idioma_y_clave(ruta)
        alternas = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{url(r)}"/>'
            for l, r in sorted(grupos[clave].items())
        ) if len(grupos[clave]) > 1 else ""
        entradas.append(f"  <url>\n    <loc>{url(ruta)}</loc>\n    <lastmod>{hoy}</lastmod>{alternas}\n  </url>")
    (salida / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(entradas) + "\n</urlset>\n",
        encoding="utf-8",
    )
    (salida / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        f"Sitemap: {SITIO}/sitemap.xml\n", encoding="utf-8",
    )
    print(f"SEO: {len(entradas)} páginas en sitemap.xml")
    return existentes
