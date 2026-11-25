// TodoPatagonia.com — JS principal

// Cargar artículos del blog desde articles.json
async function loadBlogPosts() {
  const grid = document.getElementById('blog-grid');
  if (!grid) return;

  try {
    const res = await fetch('/blog/articles.json');
    if (!res.ok) throw new Error('No se pudo cargar articles.json');
    const articles = await res.json();

    // Mostrar los últimos 3
    const recent = articles.slice(0, 3);

    grid.innerHTML = recent.map(a => `
      <article class="blog-card">
        <div class="blog-card-img">${a.emoji || '🏔️'}</div>
        <div class="blog-card-body">
          <div class="blog-card-category">${a.category || 'Guía'}</div>
          <h3>${a.title}</h3>
          <p>${a.excerpt}</p>
          <a href="/blog/${a.slug}.html" class="blog-card-link">Leer más →</a>
        </div>
      </article>
    `).join('');
  } catch (e) {
    // Si no hay artículos aún, ocultar la sección
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
  loadBlogPosts();
  initScrollHeader();
});
