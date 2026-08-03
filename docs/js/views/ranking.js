DM.renderers.ranking = function (el) {
  const { wl, card } = DM.data;
  const sectors = [...new Set(wl.map(r => r.sector))].sort();
  const statuses = [...new Set(wl.map(r => r.known_status))].sort();

  let selSectors = [], selStatuses = [], search = '', flaggedOnly = false, topN = 25;

  el.innerHTML = `
    <div class="dm-eyebrow">Company watchlist</div>
    <div class="dm-pagetitle">At-risk company ranking</div>
    <p class="dm-page-caption">Every monitored company, ranked by model risk score on its most recent
    reported period.</p>

    <div class="dm-toolbar">
      <div class="dm-field-row">
        <div class="dm-field"><label class="dm-label">Filter by sector</label><div id="rk-sector-filter"></div></div>
        <div class="dm-field"><label class="dm-label">Filter by known status</label><div id="rk-status-filter"></div></div>
      </div>
      <div class="dm-field-row">
        <div class="dm-field" style="flex:2;">
          <label class="dm-label">Search company name</label>
          <input type="text" class="dm-text" id="rk-search" placeholder="e.g. Sentoria">
        </div>
        <div class="dm-field" style="flex:0 0 auto;display:flex;align-items:center;gap:.5rem;padding-bottom:.65rem;">
          <input type="checkbox" id="rk-flagged"><label for="rk-flagged" style="font-size:.88rem;">Flagged only</label>
        </div>
      </div>
      <div class="dm-field">
        <label class="dm-label">Show top N</label>
        <input type="range" class="dm-range" id="rk-topn" min="10" max="200" step="5" value="25">
        <div class="dm-range-labels"><span id="rk-topn-val">25</span><span>10–200</span></div>
      </div>
    </div>

    <div class="dm-panel">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.1rem; gap:1rem; flex-wrap:wrap;">
        <div class="dm-panel-title" style="margin:0;">Watchlist</div>
        <button class="dm-btn" id="rk-download">⬇ Download this view as CSV</button>
      </div>
      <div class="dm-table-scroll" style="max-height:620px;"><table class="dm-table" id="rk-table"></table></div>
    </div>

    <div class="dm-card">
      <b>How to read the 'Flagged' column.</b> A company is flagged when its risk score exceeds the model's
      calibrated decision threshold (${DM.fmtNum(card.threshold)}), chosen on validation data to minimise the
      cost of mistakes — never on the test data used to measure performance. On the held-out test set this
      threshold caught ${DM.fmtPct(card.test_recall, 0)} of genuinely distressed companies at
      ${DM.fmtPct(card.test_precision, 0)} precision. Both numbers matter: most flags are worth investigating,
      and <b>most distressed companies are still missed</b>.
    </div>
  `;

  DM.createChipSelect(document.getElementById('rk-sector-filter'), {
    options: sectors, placeholder: 'Choose sector(s)…',
    onChange: (v) => { selSectors = v; render(); },
  });
  DM.createChipSelect(document.getElementById('rk-status-filter'), {
    options: statuses, placeholder: 'Choose status…',
    onChange: (v) => { selStatuses = v; render(); },
  });

  let currentDisp = [];

  function render() {
    let v = wl;
    if (selSectors.length) v = v.filter(r => selSectors.includes(r.sector));
    if (selStatuses.length) v = v.filter(r => selStatuses.includes(r.known_status));
    if (search) v = v.filter(r => r.company_name.toLowerCase().includes(search.toLowerCase()));
    if (flaggedOnly) v = v.filter(r => r.flagged);
    v = [...v].sort((a, b) => a.rank - b.rank).slice(0, topN);
    currentDisp = v;

    const tbl = document.getElementById('rk-table');
    tbl.innerHTML = `
      <thead><tr><th>#</th><th>Company</th><th>Ticker</th><th>Sector</th><th>Period end</th><th>Risk score</th>
      <th>Risk band</th><th>Flagged</th><th>Known status</th></tr></thead>
      <tbody>${v.map(r => {
        const [band] = DM.band(r.risk_percentile);
        return `<tr><td>${r.rank}</td><td>${r.company_name}</td><td>${r.ticker || '—'}</td><td>${r.sector}</td><td class="nowrap">${r.period_end}</td>
          <td>${DM.fmtNum(r.risk_score)}</td><td>${band}</td><td>${r.flagged ? 'True' : 'False'}</td>
          <td>${r.known_status}</td></tr>`;
      }).join('')}</tbody>`;
  }

  document.getElementById('rk-search').addEventListener('input', (e) => { search = e.target.value; render(); });
  document.getElementById('rk-flagged').addEventListener('change', (e) => { flaggedOnly = e.target.checked; render(); });
  document.getElementById('rk-topn').addEventListener('input', (e) => {
    topN = Number(e.target.value);
    document.getElementById('rk-topn-val').textContent = topN;
    render();
  });
  document.getElementById('rk-download').addEventListener('click', () => {
    const header = ['#', 'Company', 'Ticker', 'Sector', 'Period end', 'Risk score', 'Risk band', 'Flagged', 'Known status'];
    const rows = currentDisp.map(r => [r.rank, r.company_name, r.ticker || '', r.sector, r.period_end,
      DM.fmtNum(r.risk_score), DM.band(r.risk_percentile)[0], r.flagged, r.known_status]);
    const csv = [header, ...rows].map(row =>
      row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'bursa_distress_watchlist.csv';
    a.click();
  });

  render();
};
