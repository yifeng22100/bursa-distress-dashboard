/* Loads every CSV/JSON the app needs, once, on page load. No backend -- everything here reads
   directly from docs/data/, written by RL_Model_v1/10_build_dashboard_data.py. */

const DM = window.DM = window.DM || {};

DM.data = {};

function parseCSV(text) {
  const result = Papa.parse(text, { header: true, dynamicTyping: true, skipEmptyLines: true });
  return result.data;
}

async function fetchText(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to fetch ${path}: ${res.status}`);
  return res.text();
}

async function fetchJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to fetch ${path}: ${res.status}`);
  return res.json();
}

// booleans come out of pandas.to_csv as the literal strings "True"/"False"
function asBool(v) { return v === true || v === 'True' || v === 'TRUE'; }

DM.loadAll = async function () {
  const [wlText, secText, histText, rhText, shapText, card, gshap, metrics, weights, changes] =
    await Promise.all([
      fetchText('data/watchlist.csv'),
      fetchText('data/sector_risk.csv'),
      fetchText('data/indicator_history.csv'),
      fetchText('data/risk_history.csv'),
      fetchText('data/company_shap.csv'),
      fetchJSON('data/model_card.json'),
      fetchJSON('data/global_shap.json'),
      fetchJSON('data/model_metrics.json'),
      fetchJSON('data/model_weights.json'),
      fetchJSON('data/watchlist_changes.json').catch(() => ({ newly_flagged: [], newly_cleared: [], had_previous_run: false })),
    ]);

  const wl = parseCSV(wlText).map(r => ({ ...r, flagged: asBool(r.flagged) }));
  const sec = parseCSV(secText);
  const hist = parseCSV(histText);
  const rh = parseCSV(rhText);
  const shap = parseCSV(shapText);

  wl.sort((a, b) => a.rank - b.rank);

  DM.data = { wl, sec, hist, rh, shap, card, gshap, metrics, weights, changes };
  return DM.data;
};

DM.PRETTY = {
  current_ratio: 'Current Ratio', quick_ratio: 'Quick Ratio', cash_ratio: 'Cash Ratio',
  roa: 'Return on Assets', roe: 'Return on Equity',
  net_debt_to_total_capital: 'Net Debt / Total Capital',
  asset_turnover: 'Asset Turnover', zscore_nonmanufacturing: "Altman Z''-Score",
};

DM.pretty = function (f) {
  if (f.endsWith('_delta')) {
    const base = f.slice(0, -6);
    return (DM.PRETTY[base] || base) + ' — year-on-year change';
  }
  return DM.PRETTY[f] || f;
};

DM.band = function (pct) {
  if (pct >= 99.0) return ['Elevated', '#FF3B30', 'red'];
  if (pct >= 95.0) return ['Watch', '#FF9500', 'orange'];
  if (pct >= 80.0) return ['Moderate', '#C28800', 'gray'];
  return ['Low', '#34C759', 'green'];
};

DM.statusColor = function (status) {
  return { 'Currently PN17/GN3': 'red', 'Previously classified': 'orange',
           'No classification on record': 'gray' }[status] || 'gray';
};

DM.tag = function (text, color) {
  color = color || 'gray';
  return `<span class="dm-tag dm-tag-${color}"><span class="dm-tag-dot"></span>${text}</span>`;
};

DM.fmtPct = (v, d = 1) => (v * 100).toFixed(d) + '%';
DM.fmtNum = (v, d = 2) => Number(v).toFixed(d);
