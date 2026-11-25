document.addEventListener('click', recordAffiliateClick, { passive: true, capture: true });
document.addEventListener('auxclick', recordAffiliateClick, { passive: true, capture: true });

function recordAffiliateClick(event) {
  if (!event.isTrusted || (event.type === 'auxclick' && event.button !== 1)) return;
  const link = event.target.closest?.('a[href]');
  if (!link) return;
  const url = new URL(link.href);
  if (url.protocol !== 'https:') return;
  const partner = [
    ['booking.com', 'aid', 'booking'],
    ['getyourguide.com', 'partner_id', 'getyourguide'],
  ].find(([host, key]) =>
    (url.hostname === host || url.hostname.endsWith('.' + host)) && url.searchParams.get(key)
  );
  const bookaway = link.dataset.affiliate === 'bookaway' && url.hostname === 'www.bookaway.com';
  const provider = bookaway ? 'bookaway' : partner?.[2];
  if (!provider) return;

  const section = link.closest('[class*=-cta], section, article, aside, footer, header');
  const placement = section?.id || section?.classList[0] || section?.localName || 'body';
  const payload = JSON.stringify({
    partner: provider,
    page: location.pathname,
    placement,
  });
  if (!navigator.sendBeacon?.('/affiliate-click.php', payload)) {
    fetch('/affiliate-click.php', { method: 'POST', body: payload, keepalive: true }).catch(() => {});
  }
}
