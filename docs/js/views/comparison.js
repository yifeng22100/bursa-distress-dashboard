DM.renderers.comparison = function (el) {
  const { wl, rh, hist, shap, card } = DM.data;
  const COLORS = ['#0071E3', '#FF3B30', '#34C759', '#FF9500'];
  const sortedNames = [...wl].sort((a, b) => a.rank - b.rank).map(r => r.company_name);
  let picks = sortedNames.slice(0, 3);
  let indicator = 'current_ratio';

  el.innerHTML = `
    <div class="dm-eyebrow">Side-by-side view</div>
    <div class="dm-pagetitle">Company comparison</div>
    <p class="dm-page-caption">Put two to four companies next to each other — risk trajectory, current
    standing, and what's driving each score.</p>

    <div class="dm-toolbar">
      <div class="dm-field" style="margin-bottom:0;">
        <label class="dm-label">Companies to compare (2–4)</label>
        <div id="cmp-picker"></div>
      </div>
    </div>

    <div id="cmp-body"></div>
  `;

  const picker = DM.createChipSelect(document.getElementById('cmp-picker'), {
    options: sortedNames, selected: picks, max: 4, placeholder: 'Add a company…',
    onChange: (v) => { picks = v; render(); },
  });

  function render() {
    const body = document.getElementById('cmp-body');
    if (picks.length < 2) {
      body.innerHTML = '<div class="dm-banner dm-banner-info">Pick at least two companies to compare.</div>';
      return;
    }

    body.innerHTML = `
      <div class="dm-card-grid" style="grid-template-columns:repeat(${picks.length},1fr);" id="cmp-cards"></div>

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
        <div class="dm-card-grid" style="grid-template-columns:repeat(${picks.length},1fr);" id="cmp-shap"></div>
      </div>
    `;

    document.getElementById('cmp-cards').innerHTML = picks.map((name, i) => {
      const r = wl.find(x => x.company_name === name);
      const [lab, , bandColor] = DM.band(r.risk_percentile);
      return `<div class="dm-card" style="border-top:4px solid ${COLORS[i]};">
        <b>${name}</b><br><span style="color:var(--ink-soft);font-size:.82rem;">${r.sector}</span><br><br>
        Rank <b>#${r.rank}</b> of ${wl.length.toLocaleString()}<br>
        Score <b>${DM.fmtNum(r.risk_score)}</b><br><br>
        ${DM.tag(lab + ' risk', bandColor)}
      </div>`;
    }).join('');

    DM.plot(document.getElementById('cmp-history'),
      picks.map((name, i) => {
        const h = rh.filter(r => r.company_name === name).sort((a, b) => a.period_end < b.period_end ? -1 : 1);
        return { type: 'scatter', mode: 'lines+markers', name, x: h.map(r => r.period_end), y: h.map(r => r.risk_score),
                 line: { color: COLORS[i], width: 2 } };
      }), {
        margin: { l: 40, r: 20, t: 10, b: 40 }, yaxis: { title: 'Risk score' }, legend: { orientation: 'h', y: 1.15 },
        shapes: [{ type: 'line', x0: 0, x1: 1, xref: 'paper', y0: card.threshold, y1: card.threshold,
                   line: { color: '#6E6E73', dash: 'dash' } }],
      });

    renderIndicatorChart();

    document.getElementById('cmp-shap').innerHTML = picks.map(name => `
      <div><b>${name}</b><div id="cmp-shap-${sanitize(name)}" class="dm-chart" style="height:220px;"></div></div>
    `).join('');
    picks.forEach(name => {
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
          { margin: { l: 140, r: 10, t: 10, b: 30 } });
      } else {
        target.innerHTML = '<p class="dm-caption">No feature moved this score materially.</p>';
      }
    });

    document.getElementById('cmp-indicator').addEventListener('change', (e) => {
      indicator = e.target.value; renderIndicatorChart();
    });
  }

  function sanitize(name) { return name.replace(/[^a-z0-9]/gi, '_'); }

  function renderIndicatorChart() {
    DM.plot(document.getElementById('cmp-indchart'),
      picks.map((name, i) => {
        const h = hist.filter(r => r.company_name === name).sort((a, b) => a.period_end < b.period_end ? -1 : 1);
        return { type: 'scatter', mode: 'lines+markers', name, x: h.map(r => r.period_end), y: h.map(r => r[indicator]),
                 line: { color: COLORS[i] } };
      }), { margin: { l: 50, r: 20, t: 10, b: 40 }, yaxis: { title: DM.PRETTY[indicator] }, legend: { orientation: 'h', y: -0.2 } });
  }

  render();
};
