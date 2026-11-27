"""Descarga las fotos candidatas para la portada (Wikimedia Commons) y guarda sus créditos.

Corre en GitHub Actions (necesita internet). Guarda cada foto en img/portadas/<clave>.jpg,
a 1920 px de ancho, y los datos en data/portadas.json. La portada del sitio rota entre
las fotos de ese archivo una vez por semana (ver visuales_editoriales.py).
"""
import io
import json
import re
from html import unescape
from pathlib import Path

import requests
from PIL import Image

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "TodoPatagoniaBot/1.0 (https://todopatagonia.com; contacto@todopatagonia.com)"}
CARPETA = Path("img/portadas")
DATOS = Path("data/portadas.json")

CANDIDATAS = [
    ("fitz-roy", "Fitz Roy Chalten Argentina Todor Bozhinov 2013.jpg",
     "Cerro Fitz Roy, El Chaltén", "Mount Fitz Roy, El Chaltén", "Monte Fitz Roy, El Chaltén"),
    ("cuernos-del-paine", "Cuernos del Paine (Lago Pehoé) - panoramio.jpg",
     "Cuernos del Paine y lago Pehoé, Torres del Paine", "Cuernos del Paine and Lake Pehoé, Torres del Paine",
     "Cuernos del Paine e lago Pehoé, Torres del Paine"),
    ("laguna-de-los-tres", "Laguna de los Tres color.jpg",
     "Laguna de los Tres, El Chaltén", "Laguna de los Tres, El Chaltén", "Laguna de los Tres, El Chaltén"),
    ("perito-moreno", "Perito Moreno Glacier Front.jpg",
     "Glaciar Perito Moreno, El Calafate", "Perito Moreno Glacier, El Calafate", "Glaciar Perito Moreno, El Calafate"),
    ("cerro-torre", "Cerro torre laguna torre.jpg",
     "Cerro Torre y laguna Torre, El Chaltén", "Cerro Torre and Laguna Torre, El Chaltén", "Cerro Torre e Laguna Torre, El Chaltén"),
    ("lago-argentino", "Tèmpanos (iceberg) Lago Argentino Brazo Norte Patagonia Argentina Luca Galuzzi 2005.JPG",
     "Témpanos en el lago Argentino", "Icebergs on Lake Argentino", "Icebergs no lago Argentino"),
    ("campanario", "Cerro Campanario Bariloche Argentina - panoramio.jpg",
     "Vista desde el Cerro Campanario, Bariloche", "View from Cerro Campanario, Bariloche", "Vista do Cerro Campanario, Bariloche"),
    ("ushuaia", "Ushuaia and the Beagle Channel (5525434752).jpg",
     "Ushuaia y el Canal Beagle", "Ushuaia and the Beagle Channel", "Ushuaia e o Canal Beagle"),
    ("lacar", "Lago Lácar en San Martin de los Andes Argentina.JPG",
     "Lago Lácar, San Martín de los Andes", "Lake Lácar, San Martín de los Andes", "Lago Lácar, San Martín de los Andes"),
]


def limpiar(texto):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", texto or ""))).strip()


def main():
    CARPETA.mkdir(parents=True, exist_ok=True)
    salida = []
    for clave, archivo, es, en, pt in CANDIDATAS:
        r = requests.get(API, headers=UA, timeout=30, params={
            "action": "query", "format": "json", "titles": "File:" + archivo, "prop": "imageinfo",
            "iiprop": "url|size|extmetadata", "iiurlwidth": 1920})
        pagina = next(iter(r.json()["query"]["pages"].values()))
        info = pagina["imageinfo"][0]
        meta = info.get("extmetadata", {})
        autor = limpiar(meta.get("Artist", {}).get("value"))[:60] or "Wikimedia Commons"
        licencia = limpiar(meta.get("LicenseShortName", {}).get("value")) or "licencia libre"
        foto = Image.open(io.BytesIO(requests.get(info["thumburl"], headers=UA, timeout=60).content)).convert("RGB")
        destino = CARPETA / f"{clave}.jpg"
        foto.save(destino, "JPEG", quality=82, optimize=True, progressive=True)
        salida.append({
            "clave": clave, "imagen": "/" + destino.as_posix(), "ancho": info["width"], "alto": info["height"],
            "credito": f"{autor} · {licencia}", "fuente": info["descriptionurl"],
            "es": es, "en": en, "pt": pt, "activa": info["width"] > info["height"],
        })
        print(f"✅ {clave}: {info['width']}x{info['height']} · {autor} · {licencia}")
    DATOS.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
