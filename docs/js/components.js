/* Reusable "chip" multiselect: a text input that filters a dropdown list, picks add chips,
   chips can be removed with their own close button. Used by the ranking page's sector/status
   filters and the comparison/trends pages' company pickers. */

DM.createChipSelect = function (container, opts) {
  const { options, selected = [], max = null, placeholder = '', onChange = () => {} } = opts;
  let sel = [...selected];

  container.innerHTML = `
    <div class="dm-chipselect">
      <div class="dm-chipbox">
        <div class="dm-chips"></div>
        <input type="text" placeholder="${placeholder}" autocomplete="off">
      </div>
      <div class="dm-chip-dropdown"></div>
    </div>`;

  const chipsEl = container.querySelector('.dm-chips');
  const inputEl = container.querySelector('input');
  const dropEl = container.querySelector('.dm-chip-dropdown');

  function renderChips() {
    chipsEl.innerHTML = sel.map(v =>
      `<span class="dm-chip" data-v="${v}">${v}<button aria-label="Remove">×</button></span>`).join('');
    chipsEl.querySelectorAll('.dm-chip button').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const v = btn.parentElement.dataset.v;
        sel = sel.filter(x => x !== v);
        renderChips();
        onChange([...sel]);
      });
    });
  }

  function renderDropdown(query) {
    const q = (query || '').toLowerCase();
    const matches = options.filter(o => !sel.includes(o) && o.toLowerCase().includes(q));
    if (!matches.length) { dropEl.classList.remove('open'); dropEl.innerHTML = ''; return; }
    dropEl.innerHTML = matches.map(o => `<div class="dm-chip-option">${o}</div>`).join('');
    dropEl.classList.add('open');
    dropEl.querySelectorAll('.dm-chip-option').forEach(opt => {
      opt.addEventListener('mousedown', (e) => {
        e.preventDefault();
        if (max && sel.length >= max) return;
        sel.push(opt.textContent);
        inputEl.value = '';
        renderChips();
        renderDropdown('');
        onChange([...sel]);
      });
    });
  }

  inputEl.addEventListener('input', () => renderDropdown(inputEl.value));
  inputEl.addEventListener('focus', () => renderDropdown(inputEl.value));
  document.addEventListener('click', (e) => {
    if (!container.contains(e.target)) { dropEl.classList.remove('open'); }
  });

  renderChips();

  return {
    getSelected: () => [...sel],
    setSelected: (v) => { sel = [...v]; renderChips(); onChange([...sel]); },
  };
};
