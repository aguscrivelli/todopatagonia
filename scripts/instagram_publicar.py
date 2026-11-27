"""Publica en Instagram el siguiente post pendiente de instagram/cola.json.

Necesita las variables de entorno IG_ACCESS_TOKEN e IG_USER_ID.
Las imágenes tienen que estar ya publicadas en el sitio (las genera
instagram_render.py y las sube el deploy).

Uso: python scripts/instagram_publicar.py [--prueba]
  --prueba  muestra qué publicaría, sin publicar nada.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
COLA = RAIZ / "instagram" / "cola.json"
MEDIOS = RAIZ / "instagram" / "medios.json"
ESTADO = RAIZ / "instagram" / "publicados.json"
SITIO = "https://todopatagonia.com"
GRAPH = "https://graph.facebook.com/v23.0"
MAX_INTENTOS = 3


def cargar(ruta, defecto):
    return json.loads(ruta.read_text()) if ruta.exists() else defecto


def armar_texto(post, medio):
    partes = [post["texto"].strip()]
    if post.get("hashtags"):
        partes.append(" ".join("#" + h.lstrip("#") for h in post["hashtags"][:15]))
    partes.append(f"📷 {medio['credito']}")
    texto = "\n\n".join(partes)
    if len(texto) > 2200:
        raise ValueError(f"El texto de {post['id']} supera los 2200 caracteres")
    return texto


def llamar(metodo, ruta, token, **datos):
    # El token va en el encabezado, nunca en la URL, para que no aparezca en ningún log.
    r = requests.request(metodo, f"{GRAPH}/{ruta}", data=datos if metodo == "POST" else None,
                         params=datos if metodo == "GET" else None,
                         headers={"Authorization": f"Bearer {token}"}, timeout=60)
    cuerpo = r.json()
    if "error" in cuerpo:  # el mensaje de error de Meta no incluye el token
        err = cuerpo["error"]
        raise RuntimeError(f"API de Meta: {err.get('message')} (código {err.get('code')})")
    return cuerpo


def esperar_listo(contenedor, token):
    for _ in range(30):
        estado = llamar("GET", contenedor, token, fields="status_code").get("status_code")
        if estado == "FINISHED":
            return
        if estado in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram rechazó el contenido (estado {estado})")
        time.sleep(5)
    raise RuntimeError("Instagram tardó demasiado en procesar las imágenes")


def publicar(post, medio, token, ig_id):
    urls = [f"{SITIO}/{r}" for r in medio["imagenes"]]
    texto = armar_texto(post, medio)
    if len(urls) == 1:
        contenedor = llamar("POST", f"{ig_id}/media", token, image_url=urls[0], caption=texto)["id"]
    else:
        hijos = []
        for url in urls[:10]:
            hijo = llamar("POST", f"{ig_id}/media", token, image_url=url, is_carousel_item="true")["id"]
            esperar_listo(hijo, token)
            hijos.append(hijo)
        contenedor = llamar("POST", f"{ig_id}/media", token, media_type="CAROUSEL",
                            children=",".join(hijos), caption=texto)["id"]
    esperar_listo(contenedor, token)
    return llamar("POST", f"{ig_id}/media_publish", token, creation_id=contenedor)["id"]


def main():
    prueba = "--prueba" in sys.argv
    cola, medios, estado = cargar(COLA, []), cargar(MEDIOS, {}), cargar(ESTADO, {})
    pendientes = [
        p for p in cola
        if not estado.get(p["id"], {}).get("media_id")
        and estado.get(p["id"], {}).get("intentos", 0) < MAX_INTENTOS
        and p["id"] in medios
    ]
    if not pendientes:
        print("No hay posts pendientes con imágenes listas. Hay que cargar más en la cola.")
        return
    post = pendientes[0]
    medio = medios[post["id"]]
    print(f"Siguiente: {post['id']} ({post['tipo']}, {len(medio['imagenes'])} imagen/es). "
          f"Quedan {len(pendientes) - 1} más en la cola.")

    for r in medio["imagenes"]:
        resp = requests.head(f"{SITIO}/{r}", timeout=30, allow_redirects=True)
        if resp.status_code != 200:
            print(f"La imagen {r} todavía no está en el sitio ({resp.status_code}). Reintento en el próximo turno.")
            sys.exit(1)

    if prueba:
        print("--- MODO PRUEBA: no se publica ---")
        print(armar_texto(post, medio))
        return

    token, ig_id = os.environ.get("IG_ACCESS_TOKEN"), os.environ.get("IG_USER_ID")
    if not token or not ig_id:
        sys.exit("Faltan los secretos IG_ACCESS_TOKEN o IG_USER_ID en GitHub.")

    registro = estado.setdefault(post["id"], {})
    try:
        registro["media_id"] = publicar(post, medio, token, ig_id)
        registro["fecha"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        print(f"✅ Publicado {post['id']} (media {registro['media_id']})")
    except Exception as e:
        registro["intentos"] = registro.get("intentos", 0) + 1
        registro["ultimo_error"] = str(e)[:300]
        print(f"❌ No se pudo publicar {post['id']}: {e}")
    finally:
        ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2) + "\n")
    if not registro.get("media_id"):
        sys.exit(1)


if __name__ == "__main__":
    main()
