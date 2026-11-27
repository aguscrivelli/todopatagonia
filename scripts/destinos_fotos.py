"""Busca y descarga la foto de cada destino nuevo (Wikimedia Commons).

Para cada destino de data/destinos.json con contenido escrito y sin foto en
contenido/destinos/fotos.json, usa "foto_archivo" (nombre exacto del archivo en
Commons) o "foto_buscar" (términos de búsqueda). Guarda la foto en
img/destinos/<slug>.jpg (1600 px) y el crédito en fotos.json.
Corre en GitHub Actions (necesita internet).
"""
import json
from pathlib import Path

import requests

from generar_destinos import destinos_publicados
from instagram_render import UA, bajar, elegir_foto

FOTOS = Path("contenido/destinos/fotos.json")
CARPETA = Path("img/destinos")


def main():
    fotos = json.loads(FOTOS.read_text(encoding="utf-8")) if FOTOS.exists() else {}
    usadas = {f.get("titulo") for f in fotos.values() if f.get("titulo")}
    CARPETA.mkdir(parents=True, exist_ok=True)
    for d in destinos_publicados():
        if d["slug"] in fotos and not d.get("foto_rehacer"):
            continue
        pedido = {"archivo": d["foto_archivo"]} if d.get("foto_archivo") else {"buscar": d.get("foto_buscar", d["nombre"])}
        try:
            elegida = elegir_foto(pedido, usadas)
            imagen = bajar(elegida["url"])
        except Exception as e:
            print(f"⚠️  {d['slug']}: {e}")
            continue
        imagen.thumbnail((1600, 1600))
        ruta = CARPETA / f"{d['slug']}.jpg"
        imagen.save(ruta, "JPEG", quality=84, optimize=True, progressive=True)
        autor, _, licencia = elegida["credito"].partition(" / Wikimedia Commons ")
        fotos[d["slug"]] = {
            "url": "/" + ruta.as_posix(), "url_small": "/" + ruta.as_posix(),
            "author_name": f"{autor} {licencia}".strip(), "author_url": elegida["fuente"],
            "fuente_nombre": "Wikimedia Commons", "fuente_url": elegida["fuente"],
            "titulo": elegida["titulo"],
        }
        usadas.add(elegida["titulo"])
        print(f"✅ {d['slug']}: {elegida['titulo']} ({imagen.width}x{imagen.height})")
    FOTOS.write_text(json.dumps(fotos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
