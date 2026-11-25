"""Localized transport pilot for the El Calafate–El Chaltén route."""

RUTA = "https://www.bookaway.com"
DESTINO = "/routes/argentina/el-calafate-to-el-chalten"
GUIAS = {
    "destinos/el-chalten.html": (
        "/es", "Traslados de El Calafate a El Chaltén",
        "Compará micros, traslados compartidos y privados. Antes de reservar, verificá si la salida es desde la terminal o el aeropuerto.",
        "Comparar en Bookaway",
    ),
    "en/destinos/el-chalten.html": (
        "", "Transport from El Calafate to El Chaltén",
        "Compare buses, shared shuttles and private transfers. Before booking, check whether the service leaves from the bus terminal or the airport.",
        "Compare on Bookaway",
    ),
    "pt/destinos/el-chalten.html": (
        "/pt", "Traslados de El Calafate a El Chaltén",
        "Compare ônibus, traslados compartilhados e privativos. Antes de reservar, confira se a saída é da rodoviária ou do aeroporto.",
        "Comparar na Bookaway",
    ),
}


def agregar_traslados(path, html):
    if path not in GUIAS:
        return html
    locale, title, description, button = GUIAS[path]
    start = html.index('<section class="dest-section dest-howto">')
    end = html.index("</section>", start)
    block = f"""
        <div class="dest-booking-cta" id="traslado-calafate-chalten">
          <h3>{title}</h3>
          <p>{description}</p>
          <a class="btn-booking" href="{RUTA}{locale}{DESTINO}" data-affiliate="bookaway"
             target="_blank" rel="noopener">{button} →</a>
        </div>
      """
    return html[:end] + block + html[end:]
