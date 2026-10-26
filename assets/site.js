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
})();
