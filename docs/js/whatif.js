/* Direct JS port of app.py's mlp_forward()/score_scenario() -- same frozen 2-hidden-layer ReLU
   MLP (weights exported to data/model_weights.json as plain arrays), same robust median/IQR
   scaling. Verified against the real torch model's output to 5+ decimal places earlier in this
   project (Can-One Bhd -> 12.104739); see DM.whatifSelfTest() below, run once after data loads. */

DM.matVec = function (W, x) {
  // W: [outDim][inDim] (row-major, matches torch's Linear.weight layout), x: [inDim]
  const out = new Array(W.length).fill(0);
  for (let i = 0; i < W.length; i++) {
    let s = 0;
    const row = W[i];
    for (let j = 0; j < row.length; j++) s += row[j] * x[j];
    out[i] = s;
  }
  return out;
};

DM.addVec = (a, b) => a.map((v, i) => v + b[i]);
DM.relu = (a) => a.map(v => Math.max(0, v));

DM.mlpForward = function (x, weights) {
  const h1 = DM.relu(DM.addVec(DM.matVec(weights.w0, x), weights.b0));
  const h2 = DM.relu(DM.addVec(DM.matVec(weights.w2, h1), weights.b2));
  const out = DM.addVec(DM.matVec(weights.w4, h2), weights.b4);
  return out[2]; // 'flag' Q-value -- same index used throughout the app as risk_score
};

DM.scoreScenario = function (rawValues, weights) {
  const cols = weights.feature_cols;
  const x = cols.map(c => {
    const med = weights.medians[c], iqr = weights.iqr[c];
    let v = rawValues[c];
    if (v === undefined || v === null || Number.isNaN(v)) v = med;
    const scaled = (v - med) / iqr;
    return Math.max(-weights.clip, Math.min(weights.clip, scaled));
  });
  return DM.mlpForward(x, weights);
};

// Sanity check, run once after data loads: reproduces the same value already verified against
// the real torch model. Logs a console error (not thrown) if it ever drifts, so a bad data pull
// doesn't silently corrupt every risk score on the page.
DM.whatifSelfTest = function () {
  const { wl, hist, weights } = DM.data;
  const target = wl.find(r => r.company_name === 'Can-One Bhd');
  if (!target) return;
  const rows = hist.filter(r => r.company_name === 'Can-One Bhd').sort((a, b) => a.period_end < b.period_end ? -1 : 1);
  const latest = rows[rows.length - 1], prev = rows[rows.length - 2];
  const scenario = {};
  const FEATURES = ['current_ratio', 'quick_ratio', 'cash_ratio', 'roa', 'roe',
                     'net_debt_to_total_capital', 'asset_turnover', 'zscore_nonmanufacturing'];
  FEATURES.forEach(f => {
    scenario[f] = latest[f];
    scenario[f + '_delta'] = (prev && prev[f] != null && latest[f] != null) ? latest[f] - prev[f] : undefined;
  });
  const score = DM.scoreScenario(scenario, weights);
  const expected = Number(target.risk_score);
  const ok = Math.abs(score - expected) < 0.01;
  console[ok ? 'log' : 'error'](
    `[whatif self-test] Can-One Bhd: JS=${score.toFixed(6)} expected=${expected.toFixed(6)} ${ok ? 'OK' : 'MISMATCH'}`
  );
  return ok;
};
