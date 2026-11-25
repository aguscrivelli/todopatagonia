# TodoPatagonia.com

Sitio turístico sobre la Patagonia, generado automáticamente con IA.

## Stack

- **Sitio:** HTML/CSS estático (sin frameworks)
- **Deploy:** GitHub Actions → FTP → Hostinger
- **Contenido:** Generado automáticamente por Claude AI (cada lunes)
- **Monetización:** Booking.com afiliados + GetYourGuide + Google AdSense

## Estructura

```
├── index.html              # Página principal
├── blog/
│   ├── index.html          # Listado de artículos
│   ├── articles.json       # Base de datos de artículos
│   └── [slug].html         # Artículos generados automáticamente
├── css/
│   ├── style.css           # Estilos principales
│   └── article.css         # Estilos de artículos
├── js/main.js              # JavaScript
├── scripts/
│   └── generar_articulo.py # Generador automático de contenido
└── .github/workflows/
    ├── deploy.yml           # Deploy automático a Hostinger
    └── generar-contenido.yml # Generación semanal de artículos
```

## Secrets necesarios en GitHub

Ir a Settings → Secrets and variables → Actions y crear:

| Secret | Valor |
|--------|-------|
| `FTP_HOST` | IP del servidor Hostinger |
| `FTP_USERNAME` | Usuario FTP |
| `FTP_PASSWORD` | Contraseña FTP |
| `FTP_PATH` | `public_html` |
| `ANTHROPIC_API_KEY` | API key de Anthropic (para generación de contenido) |

## Personalización pendiente

Antes de lanzar, reemplazar en `scripts/generar_articulo.py`:
- `BOOKING_AFFILIATE = "TUAFILIADO"` → tu ID de Booking.com
- `GYG_AFFILIATE = "TUPARTNER"` → tu ID de GetYourGuide

Y en `index.html`, los links de afiliado con `aid=TUAFILIADO` y `partner_id=TUPARTNER`.

## Cómo funciona

1. Cada push a `main` dispara el workflow `deploy.yml` → sube archivos a Hostinger vía FTP
2. Cada lunes a las 9am UTC, `generar-contenido.yml` → llama a Claude AI → genera artículo → hace commit → dispara deploy
3. El resultado: artículos nuevos se publican solos cada semana sin intervención manual
