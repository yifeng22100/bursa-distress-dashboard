/* View switching: shows/hides <section class="dm-view"> elements, updates the top nav's active
   state and the URL hash (so a view is shareable/bookmarkable -- no server-side routing needed
   for a static site). Each view is rendered lazily, once, the first time it's shown. */

/* Short, single/double-word nav labels -- the full descriptive names still appear as each page's
   own <h1>. */
DM.VIEWS = [
  ['welcome', 'Home'],
  ['sector', 'Sectors'],
  ['ranking', 'Watchlist'],
  ['drilldown', 'Drill-down'],
  ['comparison', 'Compare'],
  ['trends', 'Trends'],
  ['performance', 'Performance'],
  ['about', 'About'],
];

DM.renderers = {}; // id -> function(container) -- registered by each view's js file
DM._rendered = new Set();

DM.goto = function (id) {
  if (!DM.renderers[id]) return;
  document.querySelectorAll('.dm-view').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.dm-nav button').forEach(el => el.classList.remove('active'));
  const section = document.getElementById(`view-${id}`);
  const navBtn = document.querySelector(`.dm-nav button[data-view="${id}"]`);
  if (section) section.classList.add('active');
  if (navBtn) navBtn.classList.add('active');
  if (!DM._rendered.has(id)) {
    DM.renderers[id](section);
    DM._rendered.add(id);
  }
  if (location.hash.slice(1) !== id) history.replaceState(null, '', `#${id}`);
  window.scrollTo(0, 0);
};

DM.initNav = function () {
  const navEl = document.querySelector('.dm-nav');
  navEl.innerHTML = DM.VIEWS.map(([id, label]) =>
    `<button data-view="${id}">${label}</button>`).join('');
  navEl.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => DM.goto(btn.dataset.view));
  });

  const main = document.querySelector('.dm-main');
  main.innerHTML = DM.VIEWS.map(([id]) =>
    `<section class="dm-view" id="view-${id}"></section>`).join('');

  const initial = (location.hash || '#welcome').slice(1);
  DM.goto(DM.renderers[initial] ? initial : 'welcome');
};

window.addEventListener('hashchange', () => {
  const id = location.hash.slice(1);
  if (DM.renderers[id]) DM.goto(id);
});
