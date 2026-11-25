"""Verify the three generated guides against their published copies."""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit
from urllib.request import Request, urlopen

SITE = "https://todopatagonia.com/"


class Guide(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lang = ""
        self.images = set()
        self.partners = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.lang = attrs.get("lang", "")
        if tag == "img" and attrs.get("src"):
            self.images.add(attrs["src"])
        if tag == "a" and attrs.get("href"):
            url = urlsplit(attrs["href"])
            host = url.hostname or ""
            for domain, marker in (("booking.com", "aid"), ("getyourguide.com", "partner_id")):
                if (host == domain or host.endswith("." + domain)) and url.scheme == "https" and parse_qs(url.query).get(marker):
                    self.partners.add(domain)


def fetch(url):
    return urlopen(Request(url, headers={
        "User-Agent": "TodoPatagonia Publication Check/1.0",
        "Cache-Control": "no-cache",
    }), timeout=20)


def verify(lang, path):
    path = path.lstrip("/")
    url = urljoin(SITE, path)
    with fetch(url) as response:
        html = response.read()
        if response.geturl() != url or html != (Path("_public") / path).read_bytes():
            raise ValueError("La versión pública difiere del archivo desplegado")
    guide = Guide()
    guide.feed(html.decode())
    if guide.lang.split("-")[0] != lang or len(guide.partners) != 2:
        raise ValueError("Idioma incorrecto o faltan enlaces de afiliado")
    for src in guide.images:
        with fetch(urljoin(url, src)) as image:
            if not image.headers.get_content_type().startswith("image/") or not image.read(1):
                raise ValueError(f"Imagen inválida: {src}")


def main():
    if "--existing" in sys.argv:
        guides = {lang: f"{prefix}destinos/bariloche.html"
                  for lang, prefix in (("es", ""), ("en", "en/"), ("pt", "pt/"))}
    else:
        guides = json.loads(Path(os.environ["RUNNER_TEMP"], "guias-publicadas.json").read_text())
    if set(guides) != {"es", "en", "pt"}:
        raise ValueError("Se esperaban guías en ES, EN y PT")

    pending = guides.copy()
    with ThreadPoolExecutor(max_workers=3) as pool:
        for timeout in (20, 40, 60, 0):
            jobs = {lang: pool.submit(verify, lang, path) for lang, path in pending.items()}
            for lang, job in jobs.items():
                try:
                    job.result()
                except (OSError, ValueError) as exc:
                    print(f"{lang}: {pending[lang]}: {exc}", flush=True)
                else:
                    print(f"{lang}: {pending.pop(lang)} verificada", flush=True)
            if not pending:
                return
            time.sleep(timeout)
    raise SystemExit("Falló la verificación pública: " + ", ".join(pending))


if __name__ == "__main__":
    main()
