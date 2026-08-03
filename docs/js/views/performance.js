DM.renderers.performance = function (el) {
  const { metrics, card } = DM.data;
  const cm = metrics.confusion;

  el.innerHTML = `
    <div class="dm-eyebrow">Model evaluation</div>
    <div class="dm-pagetitle">Model performance</div>
    <p class="dm-page-caption">Full evaluation of the calibrated one-step DQN on held-out 2025+ test data —
    the same numbers reported in Chapter 4 of the write-up, computed live by the same script that builds
    this dashboard.</p>

    <div class="dm-panel">
      <div class="dm-panel-title">Headline metrics</div>
      <div class="dm-card-grid cols-3">
        <div class="dm-metric"><div class="dm-metric-label">ROC-AUC</div><div class="dm-metric-value">${DM.fmtNum(metrics.roc_auc, 3)}</div></div>
        <div class="dm-metric"><div class="dm-metric-label">PR-AUC</div><div class="dm-metric-value">${DM.fmtNum(metrics.pr_auc, 3)}</div></div>
        <div class="dm-metric"><div class="dm-metric-label">F1</div><div class="dm-metric-value">${DM.fmtNum(metrics.f1_at_threshold, 3)}</div></div>
        <div class="dm-metric"><div class="dm-metric-label">Accuracy</div><div class="dm-metric-value">${DM.fmtPct(metrics.accuracy_at_threshold, 1)}</div></div>
        <div class="dm-metric"><div class="dm-metric-label">Recall</div><div class="dm-metric-value">${DM.fmtPct(card.test_recall, 1)}</div></div>
        <div class="dm-metric"><div class="dm-metric-label">Precision</div><div class="dm-metric-value">${DM.fmtPct(card.test_precision, 1)}</div></div>
      </div>
    </div>

    <div class="dm-banner dm-banner-warning">
      <b>Accuracy is misleading here — don't lean on it.</b> Only ${card.test_positives} of
      ${card.test_rows.toLocaleString()} held-out rows are genuinely distressed (0.5%), so a model that flags
      nothing at all would already score 99.5% accuracy. ROC-AUC and PR-AUC are the numbers that actually
      measure ranking quality on this imbalanced problem — and <b>PR-AUC (${DM.fmtNum(metrics.pr_auc, 3)}) is
      the honest one</b>: it stays low precisely because true positives are so rare, which is the correct
      picture for this task, not a modelling failure to hide.
    </div>

    <div class="dm-card-grid cols-2">
      <div class="dm-panel" style="margin:0;"><div class="dm-panel-title">ROC curve</div><div id="perf-roc" class="dm-chart" style="height:420px;"></div></div>
      <div class="dm-panel" style="margin:0;"><div class="dm-panel-title">Precision–recall curve</div><div id="perf-pr" class="dm-chart" style="height:420px;"></div></div>
    </div>

    <div class="dm-panel">
      <div class="dm-panel-title">Confusion matrix — DQN at calibrated threshold</div>
      <div class="dm-card-grid" style="grid-template-columns:1fr 2fr;">
        <div id="perf-cm" class="dm-chart" style="height:320px;"></div>
        <div>
          <div class="dm-card">
            <b>True positives:</b> ${cm.TP} — genuinely distressed companies correctly flagged<br>
            <b>False positives:</b> ${cm.FP} — healthy companies incorrectly flagged<br>
            <b>False negatives:</b> ${cm.FN} — genuinely distressed companies missed<br>
            <b>True negatives:</b> ${cm.TN.toLocaleString()} — healthy companies correctly left unflagged
          </div>
          <p class="dm-caption">The class imbalance is visible directly in these counts: even a well-ranking
          model produces few true positives in absolute terms, because so few company-periods are genuinely
          distressed.</p>
        </div>
      </div>
    </div>

    <div class="dm-panel">
      <div class="dm-panel-title">Cross-agent comparison</div>
      <div class="dm-table-scroll"><table class="dm-table" id="perf-agents"></table></div>
      <p class="dm-caption" style="margin-top:1.1rem;">Cost = 10×(missed distress) + 3×(false alarm) on the
      same held-out test rows for every agent. Lower is better. Figures are read directly from each agent's
      own results file, never recomputed here.</p>
    </div>
  `;

  DM.plot(document.getElementById('perf-roc'), [
    { type: 'scatter', mode: 'lines', name: `DQN (AUC=${DM.fmtNum(metrics.roc_auc, 3)})`,
      x: metrics.roc_fpr, y: metrics.roc_tpr, line: { color: '#0071E3', width: 2.5 } },
    { type: 'scatter', mode: 'lines', name: 'Chance', x: [0, 1], y: [0, 1], line: { color: '#C7C7CC', dash: 'dash' } },
    { type: 'scatter', mode: 'markers', name: "Altman Z''-Score",
      x: [metrics.altman_point.fpr], y: [metrics.altman_point.tpr], marker: { color: '#FF9500', size: 12, symbol: 'diamond' } },
    { type: 'scatter', mode: 'markers', name: 'DQN @ calibrated threshold',
      x: [metrics.own_point.fpr], y: [metrics.own_point.tpr], marker: { color: '#FF3B30', size: 12, symbol: 'star' } },
  ], { margin: { l: 50, r: 20, t: 10, b: 40 }, xaxis: { title: 'False positive rate' }, yaxis: { title: 'True positive rate' }, legend: { orientation: 'h', y: -0.25 } });

  DM.plot(document.getElementById('perf-pr'), [
    { type: 'scatter', mode: 'lines', name: `DQN (AP=${DM.fmtNum(metrics.pr_auc, 3)})`,
      x: metrics.pr_recall, y: metrics.pr_precision, line: { color: '#0071E3', width: 2.5 } },
    { type: 'scatter', mode: 'markers', name: "Altman Z''-Score",
      x: [metrics.altman_point.recall], y: [metrics.altman_point.precision], marker: { color: '#FF9500', size: 12, symbol: 'diamond' } },
  ], { margin: { l: 50, r: 20, t: 10, b: 40 }, xaxis: { title: 'Recall' }, yaxis: { title: 'Precision' }, legend: { orientation: 'h', y: -0.25 } });

  DM.plot(document.getElementById('perf-cm'), [{
    type: 'heatmap', z: [[cm.TN, cm.FP], [cm.FN, cm.TP]],
    x: ['Pred: Healthy', 'Pred: Distressed'], y: ['Actual: Healthy', 'Actual: Distressed'],
    colorscale: [[0, '#F5F5F7'], [1, '#0071E3']], showscale: false,
    text: [[cm.TN, cm.FP], [cm.FN, cm.TP]], texttemplate: '%{text:,}', textfont: { size: 18 },
  }], { margin: { l: 110, r: 10, t: 10, b: 60 } });

  const tbl = document.getElementById('perf-agents');
  tbl.innerHTML = `
    <thead><tr><th>Agent</th><th>TP</th><th>FP</th><th>FN</th><th>Recall</th><th>Precision</th><th>Cost</th></tr></thead>
    <tbody>${metrics.agent_comparison.map(a => `
      <tr><td>${a.agent}</td><td>${a.TP}</td><td>${a.FP}</td><td>${a.FN}</td>
      <td>${DM.fmtPct(a.recall, 1)}</td><td>${DM.fmtPct(a.precision, 1)}</td><td>${a.cost}</td></tr>
    `).join('')}</tbody>`;
};
