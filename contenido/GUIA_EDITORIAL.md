# Guía editorial de TodoPatagonia

Reglas para escribir artículos del blog y posts de Instagram.

## Sin datos inventados
- No nombrar hoteles, restaurantes, agencias ni operadores salvo que estén verificados.
- No poner precios, tarifas ni horarios exactos: cambian y envejecen mal. Decir "consultá la tarifa vigente".
- Distancias y tiempos, solo aproximados y conocidos ("unos 80 km", "alrededor de tres horas").
- Temporadas de fauna, siempre como períodos aproximados.
- Ante la duda, generalizar o sacar el dato.

## Formato de un artículo
Un archivo por artículo en `contenido/blog/<slug>.txt`, con una sección por idioma:

```
destination: El Calafate

=== es
title: ...
meta: ... (máx. 155 caracteres)
excerpt: ... (dos oraciones)
category: Destinos | Alojamiento | Fauna | Gastronomía | Consejos prácticos
read_time: 5
---
<h2>...</h2><p>...</p>

=== en
(category: Destinations | Accommodation | Wildlife | Food | Practical tips)

=== pt
(category: Destinos | Hospedagem | Fauna | Gastronomia | Dicas práticas)
```

- La foto, el emoji y la fecha se toman del índice del blog si el artículo ya existía. Para uno nuevo, agregar en la cabecera
  `image:`, `image_author:`, `image_source:` (Wikimedia Commons), `emoji:` y `date:`.
- Al subir el archivo, el workflow "Blog · construir artículos" arma las tres páginas y las publica.

## Tono
- Español rioplatense con voseo; inglés natural para viajeros; portugués de Brasil.
- Práctico, cálido y sin exageraciones. Cerrar con una sección de consejos prácticos.
