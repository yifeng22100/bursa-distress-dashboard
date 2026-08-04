DM.renderers.performance = function (el) {
  const { metrics, card, baselines } = DM.data;
  const cm = metrics.confusion;
  const positiveRate = card.test_positives / card.test_rows;

  // Supervised-classifier benchmark. This panel is deliberately unflattering: it is the
  // like-for-like test of whether the RL framing earns its complexity on a one-step problem,
  // and the answer here is "not clearly". Leaving it out of the artefact while it sits in the
  // write-up would contradict this dashboard's own stated principle of putting the model's
  // weaknesses on the same screen as its results.
  const baselinePanel = !baselines ? '' : `
    <div class="dm-panel">
      <div class="dm-panel-title">Benchmarked against conventional classifiers</div>
      <p class="dm-caption" style="margin:-.6rem 0 1.3rem 0;">${baselines.regime}</p>
      <div class="dm-table-scroll"><table class="dm-table" id="perf-baselines"></table></div>
      <div class="dm-banner dm-banner-warning" style="margin:1.4rem 0 0 0;">
        <b>Read this before treating the RL model as the best available option.</b>
        On misclassification cost this dashboard's DQN places
        <b>${baselines.rows.filter(r => !r.model.startsWith('Altman')).findIndex(r => r.is_this_model) + 1}
        of ${baselines.rows.filter(r => !r.model.startsWith('Altman')).length}</b>. More importantly,
        on the two threshold-free ranking measures — which is what a triage tool is actually judged
        on, and which cannot be explained away by where the decision threshold sits — it ranks below
        every tree-based method tested. Its one apparent advantage, the highest precision in the
        table, comes from a conservative threshold that flags only
        ${cm.TP + cm.FP} companies in the whole test split. The reinforcement-learning framing is
        <b>not</b> demonstrated to beat conventional supervised classification on this dataset.
        <br><br>
        This was re-tested by rolling the train/test boundary forward across three independent
        origins, re-running the entire pipeline at each one. The ranking deficit reproduced at
        <b>every</b> origin; the cost ranking did not, swinging between 2nd and 5th. That is why
        the ranking measures, not cost, carry the conclusion here.
      </div>
    </div>`;

  el.innerHTML = `
    <div class="dm-eyebrow">Model evaluation</div>
    <div class="dm-pagetitle">Model performance</div>
    <p class="dm-page-caption">Full evaluation of the calibrated one-step DQN on held-out 2025+ test data —
    computed live by the same script that builds this dashboard.</p>

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
      ${card.test_rows.toLocaleString()} held-out rows are genuinely distressed (${DM.fmtPct(positiveRate, 2)}),
      so a model that flags nothing at all would already score ${DM.fmtPct(1 - positiveRate, 2)} accuracy.
      ROC-AUC and PR-AUC are the numbers that actually
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
      <div class="dm-cm-grid">
        <div id="perf-cm" class="dm-chart" style="height:340px;"></div>
        <div class="dm-cm-stats">
          <div class="dm-cm-stat tp">
            <div class="dm-cm-stat-label">True positives</div>
            <div class="dm-cm-stat-value">${cm.TP}</div>
            <div class="dm-cm-stat-desc">Genuinely distressed, correctly flagged</div>
          </div>
          <div class="dm-cm-stat fp">
            <div class="dm-cm-stat-label">False positives</div>
            <div class="dm-cm-stat-value">${cm.FP}</div>
            <div class="dm-cm-stat-desc">Healthy companies incorrectly flagged</div>
          </div>
          <div class="dm-cm-stat fn">
            <div class="dm-cm-stat-label">False negatives</div>
            <div class="dm-cm-stat-value">${cm.FN}</div>
            <div class="dm-cm-stat-desc">Genuinely distressed, missed</div>
          </div>
          <div class="dm-cm-stat tn">
            <div class="dm-cm-stat-label">True negatives</div>
            <div class="dm-cm-stat-value">${cm.TN.toLocaleString()}</div>
            <div class="dm-cm-stat-desc">Healthy, correctly left unflagged</div>
          </div>
        </div>
      </div>
      <p class="dm-caption" style="margin-top:1.3rem;">The class imbalance is visible directly in these
      counts: even a well-ranking model produces few true positives in absolute terms, because so few
      company-periods are genuinely distressed.</p>
    </div>

    <div class="dm-panel">
      <div class="dm-panel-title">Cross-agent comparison</div>
      <div class="dm-table-scroll"><table class="dm-table" id="perf-agents"></table></div>
      <p class="dm-caption" style="margin-top:1.1rem;">Cost = 10×(missed distress) + 3×(false alarm) on the
      same held-out test rows for every agent. Lower is better. Figures are read directly from each agent's
      own results file, never recomputed here.</p>
    </div>

    ${baselinePanel}
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
  }], { margin: { l: 110, r: 10, t: 10, b: 60 }, yaxis: { automargin: true } });

  const tbl = document.getElementById('perf-agents');
  tbl.innerHTML = `
    <thead><tr><th>Agent</th><th>TP</th><th>FP</th><th>FN</th><th>Recall</th><th>Precision</th><th>Cost</th></tr></thead>
    <tbody>${metrics.agent_comparison.map(a => `
      <tr><td>${a.agent}</td><td>${a.TP}</td><td>${a.FP}</td><td>${a.FN}</td>
      <td>${DM.fmtPct(a.recall, 1)}</td><td>${DM.fmtPct(a.precision, 1)}</td><td>${a.cost}</td></tr>
    `).join('')}</tbody>`;

  if (baselines) {
    const bt = document.getElementById('perf-baselines');
    bt.innerHTML = `
      <thead><tr><th>Model</th><th>Cost</th><th>Recall</th><th>Precision</th>
      <th>ROC-AUC</th><th>95% CI</th><th>PR-AUC</th></tr></thead>
      <tbody>${baselines.rows.map(r => {
        const em = r.is_this_model
          ? ' style="background:#EAF2FE;font-weight:600;"' : '';
        const dash = '<span style="color:var(--ink-soft);">—</span>';
        return `<tr${em}>
          <td>${r.model}${r.is_this_model ? ' <span class="dm-tag dm-tag-blue">this dashboard</span>' : ''}</td>
          <td>${r.cost}</td>
          <td>${DM.fmtPct(r.recall, 1)}</td>
          <td>${DM.fmtPct(r.precision, 1)}</td>
          <td>${r.roc_auc == null ? dash : DM.fmtNum(r.roc_auc, 3)}</td>
          <td class="nowrap">${r.roc_auc_ci95 == null ? dash
            : `${DM.fmtNum(r.roc_auc_ci95[0], 3)}–${DM.fmtNum(r.roc_auc_ci95[1], 3)}`}</td>
          <td>${r.pr_auc == null ? dash : DM.fmtNum(r.pr_auc, 3)}</td>
        </tr>`;
      }).join('')}</tbody>`;
  }
};
