(() => {
  const menu = document.querySelector('.menu-btn');
  const nav = document.querySelector('.main-nav');
  const closeMenu = () => { nav?.classList.remove('open'); menu?.setAttribute('aria-expanded', 'false'); };
  menu?.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    menu.setAttribute('aria-expanded', String(open));
  });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && nav?.classList.contains('open')) { closeMenu(); menu?.focus(); } });
  document.addEventListener('click', event => { if (!nav?.contains(event.target) && !menu?.contains(event.target)) closeMenu(); });
  const form = document.querySelector('#book-filters');
  if (!form) return;
  const search = form.querySelector('#book-search');
  const genre = form.querySelector('#book-genre');
  const status = form.querySelector('#book-status');
  const cards = [...document.querySelectorAll('[data-book]')];
  const count = document.querySelector('#book-count');
  const empty = document.querySelector('#catalog-empty');
  const params = new URLSearchParams(location.search);
  search.value = params.get('q') || '';
  if ([...genre.options].some(option => option.value === params.get('genre'))) genre.value = params.get('genre');
  if ([...status.options].some(option => option.value === params.get('status'))) status.value = params.get('status');
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const filter = () => {
    const terms = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
    let shown = 0;
    cards.forEach(card => {
      const match = terms.every(term => normalize(card.dataset.search).includes(term)) && (!genre.value || card.dataset.genre === genre.value) && (!status.value || (status.value === 'forthcoming' ? card.dataset.status !== 'published' : card.dataset.status === status.value));
      card.hidden = !match;
      if (match) shown++;
    });
    count.textContent = `${shown} ${shown === 1 ? 'story' : 'stories'}${shown === cards.length ? ' to explore' : ` of ${cards.length}`}`;
    empty.hidden = shown !== 0;
    const next = new URLSearchParams();
    if (search.value.trim()) next.set('q', search.value.trim());
    if (genre.value) next.set('genre', genre.value);
    if (status.value) next.set('status', status.value);
    history.replaceState(null, '', location.pathname + (next.size ? '?' + next.toString() : ''));
  };
  form.addEventListener('submit', event => { event.preventDefault(); filter(); });
  search.addEventListener('input', filter);
  genre.addEventListener('change', filter);
  status.addEventListener('change', filter);
  document.querySelector('#reset-filters').addEventListener('click', () => { search.value = ''; genre.value = ''; status.value = ''; filter(); search.focus(); });
  filter();
})();
