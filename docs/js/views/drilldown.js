DM.renderers.drilldown = function (el) {
  const { wl, shap, rh, hist, card, weights } = DM.data;
  const FEATURES = ['current_ratio', 'quick_ratio', 'cash_ratio', 'roa', 'roe',
                     'net_debt_to_total_capital', 'asset_turnover', 'zscore_nonmanufacturing'];
  const sorted = [...wl].sort((a, b) => a.rank - b.rank);
  let current = sorted[0].company_name;

  el.innerHTML = `
    <div class="dm-eyebrow">Explainability</div>
    <div class="dm-pagetitle">Company drill-down</div>
    <div class="dm-field">
      <label class="dm-label">Select a company</label>
      <select class="dm-select" id="dd-company">
        ${sorted.map(r => `<option value="${r.company_name}">${r.company_name}</option>`).join('')}
      </select>
    </div>
    <div id="dd-body"></div>
  `;

  document.getElementById('dd-company').addEventListener('change', (e) => { current = e.target.value; renderBody(); });

  function renderBody() {
    const row = wl.find(r => r.company_name === current);
    const [lab, colr, bandColor] = DM.band(row.risk_percentile);
    const statusColor = DM.statusColor(row.known_status);

    const body = document.getElementById('dd-body');
    body.innerHTML = `
      <div class="dm-card-grid cols-2">
        <div class="dm-metric"><div class="dm-metric-label">Risk rank</div>
          <div class="dm-metric-value">#${row.rank}</div><div class="dm-metric-delta">of ${wl.length.toLocaleString()}</div></div>
        <div class="dm-metric"><div class="dm-metric-label">Risk score</div>
          <div class="dm-metric-value">${DM.fmtNum(row.risk_score)}</div><div class="dm-metric-delta">flag threshold ${DM.fmtNum(card.threshold)}</div></div>
      </div>
      <div class="dm-card-grid cols-2">
        <div class="dm-metric"><div class="dm-metric-label">Percentile</div><div class="dm-metric-value">${DM.fmtNum(row.risk_percentile, 1)}</div></div>
        <div class="dm-metric"><div class="dm-metric-label">Model action</div><div class="dm-metric-value">${row.flagged ? 'FLAG' : 'No flag'}</div></div>
      </div>
      <div class="dm-card" style="border-left:5px solid ${colr};">
        <b>${row.company_name}</b> (${row.ticker || '—'}) · ${row.sector} · period ending ${row.period_end}<br><br>
        ${DM.tag(lab + ' risk', bandColor)}${DM.tag(row.known_status, statusColor)}
      </div>

      <div class="dm-card-grid cols-2 dm-section-gap">
        <div>
          <h3>Why the model scored this company</h3>
          <div id="dd-shap" class="dm-chart" style="height:380px;"></div>
          <p class="dm-caption">Red pushes risk <b>up</b>, green pushes it <b>down</b> (SHAP contributions, this company only).</p>
        </div>
        <div>
          <h3>Risk score over time</h3>
          <div id="dd-history" class="dm-chart" style="height:380px;"></div>
          <p class="dm-caption">Periods before 2025 were used in training; 2025 onward is held-out test data.</p>
        </div>
      </div>

      <h3 class="dm-section-gap">Financial indicators</h3>
      <div class="dm-table-scroll"><table class="dm-table" id="dd-indicators"></table></div>
      <p class="dm-caption">Blank cells are genuinely missing in the source data, not zero. The model imputes
      these with the training-set median, which is itself a limitation (Chapter 5.4).</p>

      <h3 class="dm-section-gap">What-if: explore this company's risk score</h3>
      <p class="dm-caption">Nudge this company's most recent indicators and see how the model's risk score
      reacts. Runs the same frozen network used everywhere else in this dashboard, entirely in your browser
      — nothing is retrained, and nothing you enter here is saved.</p>
      <div class="dm-card-grid cols-4" id="dd-whatif-sliders"></div>
      <div class="dm-card-grid cols-3" id="dd-whatif-result"></div>
    `;

    // SHAP chart
    const srow = shap.find(r => r.company_name === current);
    if (srow) {
      const entries = FEATURES.concat(FEATURES.map(f => f + '_delta'))
        .map(f => [f, srow['shap_' + f]])
        .filter(([, v]) => Math.abs(v) > 1e-9)
        .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 10)
        .sort((a, b) => a[1] - b[1]);
      if (entries.length) {
        DM.plot(document.getElementById('dd-shap'), [{
          type: 'bar', orientation: 'h',
          x: entries.map(e => e[1]), y: entries.map(e => DM.pretty(e[0])),
          marker: { color: entries.map(e => e[1] > 0 ? '#FF3B30' : '#34C759') },
        }], { margin: { l: 220, r: 20, t: 10, b: 40 }, xaxis: { title: "Contribution to this company's risk score" } });
      } else {
        document.getElementById('dd-shap').innerHTML =
          '<p class="dm-caption">No individual feature moved this company\'s score materially away from the baseline.</p>';
      }
    }

    // Risk history chart
    const h = rh.filter(r => r.company_name === current).sort((a, b) => a.period_end < b.period_end ? -1 : 1);
    if (h.length) {
      const dd = h.filter(r => r.pn17_gn3_label === 1);
      const traces = [{
        type: 'scatter', mode: 'lines+markers', name: 'Risk score',
        x: h.map(r => r.period_end), y: h.map(r => r.risk_score), line: { color: '#0071E3', width: 2 },
      }];
      if (dd.length) traces.push({
        type: 'scatter', mode: 'markers', name: 'Actually PN17/GN3',
        x: dd.map(r => r.period_end), y: dd.map(r => r.risk_score),
        marker: { color: '#FF3B30', size: 12, symbol: 'x' },
      });
      DM.plot(document.getElementById('dd-history'), traces, {
        margin: { l: 40, r: 20, t: 10, b: 40 }, yaxis: { title: 'Risk score' },
        legend: { orientation: 'h', y: 1.15 },
        shapes: [{ type: 'line', x0: 0, x1: 1, xref: 'paper', y0: card.threshold, y1: card.threshold,
                   line: { color: '#FF3B30', dash: 'dash' } }],
      });
    }

    // Indicators table
    const ih = hist.filter(r => r.company_name === current).sort((a, b) => a.period_end < b.period_end ? -1 : 1);
    const tbl = document.getElementById('dd-indicators');
    tbl.innerHTML = `
      <thead><tr><th>Period end</th>${FEATURES.map(f => `<th>${DM.PRETTY[f]}</th>`).join('')}</tr></thead>
      <tbody>${ih.map(r => `<tr><td>${r.period_end}</td>${FEATURES.map(f =>
        `<td>${r[f] != null ? DM.fmtNum(r[f], 3) : '—'}</td>`).join('')}</tr>`).join('')}</tbody>`;

    // What-if sliders
    const latest = ih[ih.length - 1], prev = ih[ih.length - 2];
    const slidersEl = document.getElementById('dd-whatif-sliders');
    const vals = {};
    slidersEl.innerHTML = FEATURES.map(f => {
      const colVals = hist.map(r => r[f]).filter(v => v != null);
      const sortedVals = [...colVals].sort((a, b) => a - b);
      const lo = sortedVals[Math.floor(sortedVals.length * 0.02)];
      const hi = sortedVals[Math.floor(sortedVals.length * 0.98)];
      let def = latest && latest[f] != null ? latest[f] : weights.medians[f];
      def = Math.min(Math.max(def, lo), hi);
      vals[f] = def;
      return `<div class="dm-field">
        <label class="dm-label">${DM.PRETTY[f]}</label>
        <input type="range" class="dm-range whatif-slider" data-f="${f}" min="${lo}" max="${hi}" step="${(hi - lo) / 200}" value="${def}">
        <div class="dm-range-labels"><span>${DM.fmtNum(lo)}</span><span class="wv-${f}">${DM.fmtNum(def)}</span><span>${DM.fmtNum(hi)}</span></div>
      </div>`;
    }).join('');

    function recompute() {
      const scenario = {};
      FEATURES.forEach(f => {
        scenario[f] = vals[f];
        const pv = prev ? prev[f] : null;
        scenario[f + '_delta'] = (pv != null && vals[f] != null) ? vals[f] - pv : undefined;
      });
      const newScore = DM.scoreScenario(scenario, weights);
      const origScore = row.risk_score;
      const newFlag = newScore > card.threshold;
      document.getElementById('dd-whatif-result').innerHTML = `
        <div class="dm-metric"><div class="dm-metric-label">Original risk score</div><div class="dm-metric-value">${DM.fmtNum(origScore)}</div></div>
        <div class="dm-metric"><div class="dm-metric-label">What-if risk score</div><div class="dm-metric-value">${DM.fmtNum(newScore)}</div>
          <div class="dm-metric-delta">${newScore >= origScore ? '+' : ''}${DM.fmtNum(newScore - origScore)}</div></div>
        <div class="dm-metric"><div class="dm-metric-label">What-if model action</div><div class="dm-metric-value">${newFlag ? 'FLAG' : 'No flag'}</div></div>
      ` + (newFlag !== row.flagged
        ? '<div class="dm-banner dm-banner-warning" style="grid-column:1/-1;">This scenario <b>flips the flag decision</b> relative to the company\'s actual latest data.</div>'
        : '');
    }
    slidersEl.querySelectorAll('.whatif-slider').forEach(sl => {
      sl.addEventListener('input', () => {
        const f = sl.dataset.f;
        vals[f] = Number(sl.value);
        slidersEl.querySelector(`.wv-${f}`).textContent = DM.fmtNum(vals[f]);
        recompute();
      });
    });
    recompute();
  }

  renderBody();
};
