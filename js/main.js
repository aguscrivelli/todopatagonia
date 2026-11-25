// TodoPatagonia.com — JS principal

function mostrarCreditosFotos(grid, fotos) {
  if (!grid || !fotos.length) return;
  const idioma = document.documentElement.lang.slice(0, 2);
  const etiqueta = { es: 'Créditos de fotos', en: 'Photo credits', pt: 'Créditos das fotos' };
  const creditos = document.createElement('details');
  const titulo = document.createElement('summary');
  titulo.textContent = etiqueta[idioma] || etiqueta.es;
  creditos.append(titulo);
  const lista = document.createElement('ul');
  fotos.forEach(foto => {
    if (!foto.author_name || !foto.author_url) return;
    const item = document.createElement('li');
    const enlace = document.createElement('a');
    enlace.href = foto.author_url;
    enlace.textContent = foto.alt + ' — ' + foto.author_name;
    item.append(enlace);
    lista.append(item);
  });
  if (lista.childElementCount) {
    creditos.append(lista);
    grid.after(creditos);
  }
}

// Cargar fotos de destinos desde el JSON pre-generado
async function loadDestinationPhotos() {
  const cards = document.querySelectorAll('.dest-card[data-dest]');
  if (!cards.length) return;

  try {
    const res = await fetch('/data/destination-photos.json?v=20261125');
    if (!res.ok) return; // sin JSON: quedará con gradiente+emoji
    const photos = await res.json();

    cards.forEach(card => {
      const dest = card.getAttribute('data-dest');
      const photo = photos[dest];
      if (!photo) return;

      const imgContainer = card.querySelector('.dest-img');
      const img = document.createElement('img');
      img.src = photo.url;
      img.alt = photo.alt || dest;
      img.loading = 'lazy';
      img.onload = () => imgContainer.classList.add('loaded');
      img.onerror = () => {}; // fallback: se ve el emoji
      imgContainer.appendChild(img);
    });
    mostrarCreditosFotos(document.getElementById('dest-grid'), Object.values(photos));
  } catch (e) {
    // Sin fotos: se muestran los emojis de fallback, sin problema
  }
}

// Cargar artículos del blog desde articles.json
// Soporta múltiples idiomas: las páginas EN/PT definen BLOG_JSON y BLOG_BASE
async function loadBlogPosts() {
  const grid = document.getElementById('blog-grid');
  if (!grid) return;

  // Si la página define BLOG_JSON (en/ o pt/), usarlo; si no, español por defecto
  const jsonUrl = (typeof BLOG_JSON !== 'undefined') ? BLOG_JSON : '/blog/articles.json';
  const blogBase = (typeof BLOG_BASE !== 'undefined') ? BLOG_BASE : '/blog/';

  // Textos "Leer más" según idioma
  const readMoreLabels = {
    '/blog/': 'Leer más →',
    '/en/blog/': 'Read more →',
    '/pt/blog/': 'Ler mais →',
  };
  const readMore = readMoreLabels[blogBase] || 'Leer más →';

  try {
    const res = await fetch(jsonUrl, { cache: "no-cache" });
    if (!res.ok) throw new Error('No articles.json yet');
    const articles = await res.json();

    const recent = articles.slice(0, 3);

    grid.innerHTML = recent.map(a => {
      const imgHtml = a.image_url
        ? `<img src="${a.image_url}" alt="${a.title}" class="blog-card-photo" loading="lazy">`
        : `<div class="blog-card-emoji">${a.emoji || '🏔️'}</div>`;
      return `
        <article class="blog-card">
          <div class="blog-card-img">${imgHtml}</div>
          <div class="blog-card-body">
            <div class="blog-card-category">${a.category || 'Guide'}</div>
            <h3>${a.title}</h3>
            <p>${a.excerpt}</p>
            <a href="${a.url || `${blogBase}${a.slug}.html`}" class="blog-card-link">${readMore}</a>
            ${a.image_source ? `<small class="blog-card-credit"><a href="${a.image_source}">${a.image_author}</a></small>` : ""}
          </div>
        </article>`;
    }).join('');
  } catch (e) {
    const section = grid.closest('.section');
    if (section) section.style.display = 'none';
  }
}

// Header: opacar al hacer scroll
function initScrollHeader() {
  const header = document.querySelector('.site-header');
  if (!header) return;
  window.addEventListener('scroll', () => {
    if (window.scrollY > 60) {
      header.style.boxShadow = '0 4px 20px rgba(0,0,0,0.25)';
    } else {
      header.style.boxShadow = '0 2px 12px rgba(0,0,0,0.15)';
    }
  }, { passive: true });
}

document.addEventListener('DOMContentLoaded', () => {
  loadDestinationPhotos();
  loadBlogPosts();
  initScrollHeader();
});
