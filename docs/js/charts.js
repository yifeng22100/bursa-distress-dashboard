/* Shared Plotly.js helpers. Views build their own trace arrays (same shape as the Python Plotly
   code they're ported from) and pass them through these small wrappers for consistent styling. */

DM.PLOTLY_CFG = { displayModeBar: false, responsive: true };

DM.baseLayout = function (extra) {
  return Object.assign({
    plot_bgcolor: 'rgba(0,0,0,0)', paper_bgcolor: 'rgba(0,0,0,0)',
    font: { family: '-apple-system, BlinkMacSystemFont, Inter, sans-serif', color: '#1D1D1F', size: 12 },
    margin: { l: 40, r: 20, t: 20, b: 40 },
  }, extra || {});
};

DM.plot = function (el, traces, layout) {
  Plotly.newPlot(el, traces, DM.baseLayout(layout), DM.PLOTLY_CFG);
};
