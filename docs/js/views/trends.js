DM.renderers.trends = function (el) {
  const { wl, hist } = DM.data;
  const sortedNames = [...wl].sort((a, b) => a.rank - b.rank).map(r => r.company_name);
  let indicator = 'current_ratio';
  let picks = sortedNames.slice(0, 5);

  el.innerHTML = `
    <div class="dm-eyebrow">Trend analysis</div>
    <div class="dm-pagetitle">Indicator trends</div>
    <p class="dm-page-caption">Compare a financial indicator over time across companies.</p>

    <div class="dm-toolbar">
      <div class="dm-field" style="max-width:420px;">
        <label class="dm-label">Indicator</label>
        <select class="dm-select" id="tr-indicator">
          ${Object.keys(DM.PRETTY).map(k => `<option value="${k}">${DM.PRETTY[k]}</option>`).join('')}
        </select>
      </div>
      <div class="dm-field" style="margin-bottom:0;">
        <label class="dm-label">Companies (default: current top 5 by risk)</label>
        <div id="tr-picker"></div>
      </div>
    </div>

    <div class="dm-panel">
      <div id="tr-chart" class="dm-chart" style="height:520px;"></div>
      <p class="dm-caption" id="tr-caption" style="margin-top:1.1rem;"></p>
    </div>
    <div class="dm-banner dm-banner-info" id="tr-zscore-note" style="display:none;">
      The Altman Z''-Score distress threshold is 1.1. This project's own benchmark analysis found it
      flags 13% of all Bursa company-periods — high recall, low precision.
    </div>
  `;

  DM.createChipSelect(document.getElementById('tr-picker'), {
    options: sortedNames, selected: picks, placeholder: 'Add a company…',
    onChange: (v) => { picks = v; render(); },
  });

  function render() {
    const chartEl = document.getElementById('tr-chart');
    if (!picks.length) { chartEl.innerHTML = ''; document.getElementById('tr-caption').textContent = ''; return; }

    const traces = picks.map(name => {
      const h = hist.filter(r => r.company_name === name).sort((a, b) => a.period_end < b.period_end ? -1 : 1);
      return { type: 'scatter', mode: 'lines+markers', name, x: h.map(r => r.period_end), y: h.map(r => r[indicator]) };
    });
    const marked = hist.filter(r => picks.includes(r.company_name) && r.pn17_gn3_label === 1);
    if (marked.length) traces.push({
      type: 'scatter', mode: 'markers', name: 'PN17/GN3 period',
      x: marked.map(r => r.period_end), y: marked.map(r => r[indicator]),
      marker: { color: '#FF3B30', size: 13, symbol: 'x' },
    });
    DM.plot(chartEl, traces, {
      margin: { l: 50, r: 20, t: 10, b: 40 }, yaxis: { title: DM.PRETTY[indicator] },
      legend: { orientation: 'h', y: -0.2 },
    });
    document.getElementById('tr-caption').textContent =
      "Red ✕ marks a period in which the company was officially PN17/GN3-classified. Gaps are missing data.";
    document.getElementById('tr-zscore-note').style.display = indicator === 'zscore_nonmanufacturing' ? 'block' : 'none';
  }

  document.getElementById('tr-indicator').addEventListener('change', (e) => { indicator = e.target.value; render(); });
  render();
};
