"""Regla: ningún texto visible de una página puede estar en otro idioma.

Recorre las páginas del sitio armado y, en cada bloque de texto, cuenta
palabras típicas de español, inglés y portugués (sin contar nombres propios).
Si un bloque está claramente en un idioma distinto al de la página, frena la
publicación y muestra dónde está el problema.

Excepciones (nombres propios, citas): una línea por texto en
contenido/idiomas_permitidos.txt.

Uso: python scripts/verificar_idiomas.py [carpeta]   (por defecto _public)
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# Solo palabras que distinguen un idioma de los otros dos.
PALABRAS = {
    "es": set("""el la los las del y en con una un es su sus al lo más muy desde hasta también pero
        disponibles consejos días cerca tu tus están hay esta este estos estas sin donde cuándo cuando
        según mejor incluye hoteles cabañas excursiones cancelación mayoría planificar moverse reservá
        podés tenés hacé llevá elegí guía guías nuestro nuestra ver más leer pasos fronterizos""".split()),
    "en": set("""the and of to in for with is on your from are you this that these those it its be can
        by at an or more most best near our their through around which when where while will what how
        get see read book find""".split()),
    "pt": set("""o os do da dos das e em com uma um é seu sua seus suas ao aos no na nos nas não você
        mais muito também mas dicas dias perto até estão há sem onde quando melhor inclui hotéis cabanas
        passeios cancelamento maioria planejar ler nosso nossa guia""".split()),
}
# Palabras que existen en dos idiomas y confunden: se ignoran.
for ambigua in ("a", "de", "que", "para", "por", "se", "como", "entre", "sobre", "cada", "está", "ver", "mais"):
    for v in PALABRAS.values():
        v.discard(ambigua)


# Textos cortos de interfaz que delatan una mezcla aunque tengan pocas palabras.
FRASES = {
    "es": ["Ver tours disponibles", "¿Cuándo ir?", "¿Cómo moverse?", "Leer más", "Por destino",
           "Aeropuerto:", "Desde Buenos Aires:", "Transporte local:", "Última actualización",
           "Consejos para", "Reservá ", "Cómo llegar"],
    "en": ["Read more", "When to go", "Getting around", "By destination", "Last updated",
           "Book your", "Find your", "How to get there", "See available"],
    "pt": ["Ler mais", "Quando ir", "Como se locomover", "Última atualização", "Dicas para",
           "Reserve sua", "Como chegar", "Ver passeios"],
}
COMPARTIDAS_ES_PT = {"Por destino", "Transporte local:"}
MESES_EN = r"\b(January|February|March|April|June|July|August|September|October|November|December)\b"
MESES_ES_PT = (r"\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre"
               r"|janeiro|fevereiro|março|maio|junho|julho|setembro|outubro|novembro|dezembro)\b")
TRILINGUE = re.compile(r"\w+ / (Easy|Moderate|Difficult) / \w+")


class Texto(HTMLParser):
    def __init__(self):
        super().__init__()
        self.saltar = 0
        self.bloques = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "code"):
            self.saltar += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "code") and self.saltar:
            self.saltar -= 1

    def handle_data(self, data):
        if not self.saltar and data.strip():
            self.bloques.append(" ".join(data.split()))


def idioma_pagina(ruta):
    return "en" if ruta.startswith("en/") else "pt" if ruta.startswith("pt/") else "es"


def puntajes(texto):
    palabras = re.findall(r"[A-Za-zÁÉÍÓÚÑÃÕÇÂÊÔÀáéíóúñãõçâêôàü]+", texto)
    # Fuera los nombres propios: palabras con mayúscula que no abren la frase.
    comunes = [p.lower() for i, p in enumerate(palabras) if i == 0 or not p[0].isupper()]
    return {l: sum(p in v for p in comunes) for l, v in PALABRAS.items()}, len(comunes)


def revisar(carpeta):
    carpeta = Path(carpeta)
    permitidos = set()
    archivo = Path("contenido/idiomas_permitidos.txt")
    if archivo.exists():
        permitidos = {l.strip() for l in archivo.read_text(encoding="utf-8").splitlines()
                      if l.strip() and not l.startswith("#")}
    problemas = []
    for pagina in sorted(carpeta.rglob("*.html")):
        ruta = pagina.relative_to(carpeta).as_posix()
        if ruta.startswith("ig") or ruta.startswith("google"):
            continue
        propio = idioma_pagina(ruta)
        parser = Texto()
        parser.feed(pagina.read_text(encoding="utf-8"))
        for bloque in parser.bloques:
            if bloque in permitidos:
                continue
            for lang, frases in FRASES.items():
                if lang == propio:
                    continue
                if lang == "es" and propio == "pt":  # frases que se escriben igual en portugués
                    frases = [f for f in frases if f not in COMPARTIDAS_ES_PT]
                if any(f in bloque for f in frases):
                    problemas.append((ruta, lang, bloque[:120]))
            if TRILINGUE.search(bloque):
                problemas.append((ruta, "mezcla", bloque[:120]))
            if propio != "en" and re.search(MESES_EN, bloque):
                problemas.append((ruta, "en", bloque[:120]))
            # En minúscula: así "28 de Julio" (un nombre propio) no cuenta como mes.
            if propio == "en" and re.search(MESES_ES_PT, bloque):
                problemas.append((ruta, "es/pt", bloque[:120]))
            p, n = puntajes(bloque)
            if n < 2:
                continue
            otro = max(p, key=p.get)
            if otro != propio and p[otro] >= 2 and p[otro] >= p[propio] + 2:
                problemas.append((ruta, otro, bloque[:120]))
    return problemas


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "_public"
    problemas = revisar(carpeta)
    if not problemas:
        print("Idiomas: sin mezclas.")
        return
    print(f"❌ Idiomas: {len(problemas)} textos en otro idioma. No se publica hasta corregirlos:")
    for ruta, otro, texto in problemas:
        print(f"  {ruta} [{otro}] {texto}")
    print("Si alguno es un nombre propio o una excepción válida, agregalo a contenido/idiomas_permitidos.txt")
    sys.exit(1)


if __name__ == "__main__":
    main()
