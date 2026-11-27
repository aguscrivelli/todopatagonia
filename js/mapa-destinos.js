/* Mapa de destinos de TodoPatagonia.
   Base cartográfica oficial del Instituto Geográfico Nacional (Argenmap),
   que representa a las Islas Malvinas como territorio argentino. */
(function () {
  const caja = document.getElementById('mapa-patagonia');
  if (!caja || typeof L === 'undefined') return;

  const lang = (document.documentElement.lang || 'es').slice(0, 2);
  const base = { es: '/destinos/', en: '/en/destinos/', pt: '/pt/destinos/' }[lang] || '/destinos/';
  const verGuia = { es: 'Ver guía →', en: 'View guide →', pt: 'Ver guia →' }[lang] || 'Ver guía →';

  const mapa = L.map(caja, { scrollWheelZoom: false, minZoom: 3, maxZoom: 12 });
  mapa.attributionControl.setPrefix('<a href="https://leafletjs.com" target="_blank" rel="noopener">Leaflet</a>');
  // Etiquetas a la izquierda donde los puntos quedan muy cerca.
  const lado = { 'torres-del-paine': 'left', 'el-chalten': 'left' };
  L.tileLayer('https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/capabaseargenmap@EPSG%3A3857@png/{z}/{x}/{y}.png', {
    tms: true,
    attribution: '<a href="https://www.ign.gob.ar" target="_blank" rel="noopener">Instituto Geográfico Nacional</a>',
  }).addTo(mapa);

  // Patagonia continental, Tierra del Fuego e Islas Malvinas.
  mapa.fitBounds([[-55.3, -77.5], [-38.5, -57.0]], { padding: [10, 10] });

  fetch('/data/destinos.json')
    .then((r) => r.json())
    .then((datos) => {
      datos.activos.filter((d) => d.lat && d.lng).forEach((d) => {
        const desc = d['descripcion_' + lang] || d.descripcion_es;
        L.circleMarker([d.lat, d.lng], {
          radius: 9, color: '#fff', weight: 2, fillColor: '#d4650a', fillOpacity: 1,
        })
          .addTo(mapa)
          .bindTooltip(d.nombre, { permanent: true, direction: lado[d.slug] || 'right', offset: [lado[d.slug] ? -10 : 10, 0], className: 'mapa-etiqueta' })
          .bindPopup(
            `<strong>${d.emoji} ${d.nombre}</strong><p>${desc}</p><a href="${base}${d.slug}.html">${verGuia}</a>`
          );
      });
    })
    .catch(() => {});
})();
