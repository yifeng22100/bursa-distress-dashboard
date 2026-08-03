DM.renderers.sector = function (el) {
  const { sec } = DM.data;
  const METRIC_LABELS = {
    median_risk: 'Median risk score (recommended)', mean_risk: 'Mean risk score',
    flagged_pct: '% of companies flagged',
  };
  const SHORT = { median_risk: 'Median', mean_risk: 'Mean', flagged_pct: '% flagged' };
  let metric = 'median_risk', minN = 5;

  el.innerHTML = `
    <div class="dm-eyebrow">Risk monitoring</div>
    <div class="dm-pagetitle">Sector risk overview</div>
    <p class="dm-page-caption">Model risk score aggregated by sector, across each company's most recent
    reported period. Use this to decide where to look first — not as a verdict on any sector.</p>

    <div class="dm-field-row">
      <div class="dm-field">
        <label class="dm-label">Rank sectors by</label>
        <select class="dm-select" id="sec-metric">
          ${Object.entries(METRIC_LABELS).map(([k, v]) => `<option value="${k}">${v}</option>`).join('')}
        </select>
      </div>
      <div class="dm-field" style="flex:2;">
        <label class="dm-label">Minimum companies in sector</label>
        <input type="range" class="dm-range" id="sec-minn" min="1" max="20" value="5">
        <div class="dm-range-labels"><span id="sec-minn-val">5</span><span>1–20</span></div>
      </div>
    </div>

    <div id="sec-chart" class="dm-chart" style="height:520px;"></div>

    <h3 class="dm-section-gap">Highest-risk sectors</h3>
    <div class="dm-table-scroll"><table class="dm-table" id="sec-table"></table></div>

    <div class="dm-banner dm-banner-info dm-section-gap" id="sec-info"></div>
    <div class="dm-banner dm-banner-warning" id="sec-warn" style="display:none;"></div>
  `;

  function render() {
    const viewSec = sec.filter(r => r.companies >= minN);
    const hidden = sec.filter(r => r.companies < minN);
    const top = [...viewSec].sort((a, b) => b[metric] - a[metric]).slice(0, 15);
    const topAsc = [...top].reverse(); // ascending for horizontal bar (largest at top)

    const vals = topAsc.map(r => r[metric]);
    const lo = Math.min(...vals), hi = Math.max(...vals);
    const colorAt = (v) => {
      const t = hi === lo ? 0.5 : (v - lo) / (hi - lo);
      const stops = ['#34C759', '#C28800', '#FF9500', '#FF3B30'];
      const idx = Math.min(stops.length - 2, Math.floor(t * (stops.length - 1)));
      return stops[idx + (t * (stops.length - 1) - idx > 0.5 ? 1 : 0)];
    };

    DM.plot(document.getElementById('sec-chart'), [{
      type: 'bar', orientation: 'h',
      x: vals, y: topAsc.map(r => r.sector),
      marker: { color: vals.map(colorAt) },
      hovertemplate: '%{y}<br>' + SHORT[metric] + ': %{x:.2f}<extra></extra>',
    }], { margin: { l: 260, r: 20, t: 10, b: 40 }, xaxis: { title: METRIC_LABELS[metric].replace(' (recommended)', '') } });

    const tbl = document.getElementById('sec-table');
    tbl.innerHTML = `
      <thead><tr><th>Sector</th><th>Cos.</th><th>${SHORT[metric]}</th><th>PN17</th></tr></thead>
      <tbody>${top.map(r => `
        <tr><td>${r.sector}</td><td>${r.companies}</td><td>${DM.fmtNum(r[metric])}</td><td>${r.currently_distressed}</td></tr>
      `).join('')}</tbody>`;

    document.getElementById('sec-info').innerHTML =
      `<b>Why median, and why a minimum size.</b> A sector's <i>mean</i> risk is easily dominated by one or
      two extreme companies, and a sector holding three firms can top any ranking by chance — so the default
      view uses the median and hides sectors with fewer than ${minN} companies (${hidden.length}
      sector${hidden.length !== 1 ? 's' : ''} hidden at this setting). Switch the controls above to see the
      alternatives; the 'Cos.' column is shown so sector size is always visible.`;

    const uncl = sec.find(r => r.sector.startsWith('(not classified'));
    const warnEl = document.getElementById('sec-warn');
    if (uncl && uncl.companies) {
      warnEl.style.display = 'block';
      warnEl.innerHTML = `<b>${uncl.companies} companies carry no sector classification</b> and appear as
        their own bucket. These are the delisted-firm supplement records (Chapter 3), and
        ${uncl.currently_distressed} of them are genuinely distressed — so excluding them, which earlier
        drafts of this analysis did, would make the sector picture look better than it is.`;
    }
  }

  document.getElementById('sec-metric').addEventListener('change', (e) => { metric = e.target.value; render(); });
  document.getElementById('sec-minn').addEventListener('input', (e) => {
    minN = Number(e.target.value);
    document.getElementById('sec-minn-val').textContent = minN;
    render();
  });
  render();
};
