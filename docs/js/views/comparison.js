DM.renderers.comparison = function (el) {
  const { wl, rh, hist, shap, card } = DM.data;
  const COLORS = ['#0071E3', '#FF3B30', '#34C759', '#FF9500'];
  const SLOTS = 4;
  const sortedNames = [...wl].sort((a, b) => a.rank - b.rank).map(r => r.company_name);
  let picks = [sortedNames[0], sortedNames[1], sortedNames[2], undefined];
  let indicator = 'current_ratio';

  el.innerHTML = `
    <div class="dm-eyebrow">Side-by-side view</div>
    <div class="dm-pagetitle">Company comparison</div>
    <p class="dm-page-caption">Put two to four companies next to each other — risk trajectory, current
    standing, and what's driving each score.</p>

    <div class="dm-panel">
      <div class="dm-panel-title">Compare companies</div>
      <p class="dm-caption" style="margin:-.6rem 0 1.3rem 0;">Add 2 to 4 companies below, or start from any
      company's <b>Drill-down</b> page.</p>
      <div class="dm-slotrow" id="cmp-slots"></div>
    </div>

    <div id="cmp-body"></div>
  `;

  function active() { return picks.filter(Boolean); }

  function renderSlots() {
    const row = document.getElementById('cmp-slots');
    row.innerHTML = '';
    for (let i = 0; i < SLOTS; i++) {
      const name = picks[i];
      const slot = document.createElement('div');
      if (name) {
        const r = wl.find(x => x.company_name === name);
        const [lab, , bandColor] = DM.band(r.risk_percentile);
        slot.className = 'dm-slot filled';
        slot.style.borderTopColor = COLORS[i];
        slot.innerHTML = `
          <button class="dm-slot-remove" aria-label="Remove ${name}">×</button>
          <div class="dm-slot-name">${name}${r.ticker ? ` <span style="font-weight:400;color:var(--ink-soft);">(${r.ticker})</span>` : ''}</div>
          <div class="dm-slot-sector">${r.sector}</div>
          <div class="dm-slot-meta">Rank <b>#${r.rank}</b> · Score <b>${DM.fmtNum(r.risk_score)}</b></div>
          ${DM.tag(lab + ' risk', bandColor)}
        `;
        slot.querySelector('.dm-slot-remove').addEventListener('click', () => {
          picks[i] = undefined; renderSlots(); render();
        });
      } else {
        slot.className = 'dm-slot';
        slot.innerHTML = `<span class="dm-slot-plus">+</span><span>Slot ${i + 1}</span>`;
        slot.addEventListener('click', () => openSlotSearch(i));
      }
      row.appendChild(slot);
    }
  }

  function openSlotSearch(i) {
    const row = document.getElementById('cmp-slots');
    const slot = row.children[i];
    slot.className = 'dm-slot searching';
    slot.innerHTML = `<input type="text" class="dm-slot-input" placeholder="Search company…" autocomplete="off">
      <div class="dm-slot-dropdown"></div>`;
    const input = slot.querySelector('input');
    const drop = slot.querySelector('.dm-slot-dropdown');
    const chosen = new Set(picks.filter(Boolean));

    function renderOpts(q) {
      const query = (q || '').toLowerCase();
      const matches = sortedNames.filter(n => !chosen.has(n) && n.toLowerCase().includes(query));
      drop.innerHTML = matches.map(n => `<div class="dm-slot-option">${n}</div>`).join('');
      drop.querySelectorAll('.dm-slot-option').forEach(opt => {
        opt.addEventListener('mousedown', (e) => {
          e.preventDefault();
          picks[i] = opt.textContent;
          renderSlots(); render();
        });
      });
    }
    renderOpts('');
    input.addEventListener('input', () => renderOpts(input.value));
    input.addEventListener('blur', () => setTimeout(() => { if (!picks[i]) renderSlots(); }, 150));
    input.focus();
  }

  function render() {
    const names = active();
    renderSlots();
    const body = document.getElementById('cmp-body');
    if (names.length < 2) {
      body.innerHTML = '<div class="dm-banner dm-banner-info">Pick at least two companies above to compare.</div>';
      return;
    }

    body.innerHTML = `
      <div class="dm-panel">
        <div class="dm-panel-title">Risk score over time</div>
        <div id="cmp-history" class="dm-chart" style="height:420px;"></div>
      </div>

      <div class="dm-panel">
        <div class="dm-panel-title">Indicator comparison</div>
        <div class="dm-field" style="max-width:320px;">
          <select class="dm-select" id="cmp-indicator">
            ${Object.keys(DM.PRETTY).map(k => `<option value="${k}" ${k === indicator ? 'selected' : ''}>${DM.PRETTY[k]}</option>`).join('')}
          </select>
        </div>
        <div id="cmp-indchart" class="dm-chart" style="height:380px;"></div>
      </div>

      <div class="dm-panel">
        <div class="dm-panel-title">What's driving each score</div>
        <div class="dm-card-grid cols-2" id="cmp-shap"></div>
      </div>
    `;

    DM.plot(document.getElementById('cmp-history'),
      names.map((name, i) => {
        const h = rh.filter(r => r.company_name === name).sort((a, b) => a.period_end < b.period_end ? -1 : 1);
        return { type: 'scatter', mode: 'lines+markers', name, x: h.map(r => r.period_end), y: h.map(r => r.risk_score),
                 line: { color: COLORS[i], width: 2 } };
      }), {
        margin: { l: 40, r: 20, t: 10, b: 40 }, yaxis: { title: 'Risk score' }, legend: { orientation: 'h', y: 1.15 },
        shapes: [{ type: 'line', x0: 0, x1: 1, xref: 'paper', y0: card.threshold, y1: card.threshold,
                   line: { color: '#6E6E73', dash: 'dash' } }],
      });

    renderIndicatorChart(names);

    document.getElementById('cmp-shap').innerHTML = names.map(name => `
      <div><b>${name}</b><div id="cmp-shap-${sanitize(name)}" class="dm-chart" style="height:260px;"></div></div>
    `).join('');
    names.forEach(name => {
      const srow = shap.find(r => r.company_name === name);
      const target = document.getElementById(`cmp-shap-${sanitize(name)}`);
      if (!srow) return;
      const FEATURES = ['current_ratio', 'quick_ratio', 'cash_ratio', 'roa', 'roe',
                         'net_debt_to_total_capital', 'asset_turnover', 'zscore_nonmanufacturing'];
      const entries = FEATURES.concat(FEATURES.map(f => f + '_delta'))
        .map(f => [f, srow['shap_' + f]]).filter(([, v]) => Math.abs(v) > 1e-9)
        .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 5).sort((a, b) => a[1] - b[1]);
      if (entries.length) {
        DM.plot(target, [{ type: 'bar', orientation: 'h', x: entries.map(e => e[1]), y: entries.map(e => DM.pretty(e[0])),
          marker: { color: entries.map(e => e[1] > 0 ? '#FF3B30' : '#34C759') } }],
          { margin: { l: 140, r: 10, t: 10, b: 30 }, yaxis: { automargin: true } });
      } else {
        target.innerHTML = '<p class="dm-caption">No feature moved this score materially.</p>';
      }
    });

    document.getElementById('cmp-indicator').addEventListener('change', (e) => {
      indicator = e.target.value; renderIndicatorChart(active());
    });
  }

  function sanitize(name) { return name.replace(/[^a-z0-9]/gi, '_'); }

  function renderIndicatorChart(names) {
    DM.plot(document.getElementById('cmp-indchart'),
      names.map((name, i) => {
        const h = hist.filter(r => r.company_name === name).sort((a, b) => a.period_end < b.period_end ? -1 : 1);
        return { type: 'scatter', mode: 'lines+markers', name, x: h.map(r => r.period_end), y: h.map(r => r[indicator]),
                 line: { color: COLORS[i] } };
      }), { margin: { l: 50, r: 20, t: 10, b: 40 }, yaxis: { title: DM.PRETTY[indicator] }, legend: { orientation: 'h', y: -0.2 } });
  }

  render();
};
