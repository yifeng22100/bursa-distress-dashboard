DM.renderers.about = function (el) {
  const { card, gshap } = DM.data;
  const PROJECT_TITLE = "A Reinforcement Learning Approach to Corporate Financial Distress Prediction — Feature Importance Analysis of Bursa Malaysia Listed Companies";
  const PROJECT_CODE = "PRJ5158 · MsBA Capstone II · Sunway Business School";
  const TEAM = ["Jeremy Choong Ming", "Tan Yan Sheng", "Tan Yi Feng"];
  const beats = card.recall_matched_beats_benchmark;

  el.innerHTML = `
    <div class="dm-eyebrow">Project overview</div>
    <div class="dm-pagetitle">About & Methodology</div>

    <div class="dm-card" style="padding:2.2rem 2.4rem; background:linear-gradient(135deg, #EAF2FE, #FFFFFF); border-color:#C7DFFB;">
      <div class="dm-eyebrow" style="margin-bottom:.9rem;">${PROJECT_CODE}</div>
      <h4 style="margin:0 0 1.1rem 0; font-size:1.4rem; line-height:1.35;">${PROJECT_TITLE}</h4>
      <div style="display:flex; gap:.5rem; flex-wrap:wrap;">
        ${TEAM.map(t => `<span class="dm-tag" style="background:#fff;border-color:#C7DFFB;color:#0058C6;">${t}</span>`).join('')}
      </div>
    </div>

    <p>This dashboard is the artefact deliverable for <b>RQ4</b> of the capstone. It presents the output of
    reinforcement learning agents trained to flag Bursa Malaysia companies at risk of PN17/GN3
    classification, benchmarked against the classical Altman Z''-Score model.</p>

    <h3 class="dm-section-gap">What this dashboard does</h3>
    <div class="dm-card-grid cols-3">
      <div class="dm-card" style="margin-bottom:0;">🔎 <b>Monitor.</b> Every listed company is scored on its
      most recent reported financials and ranked by model risk score, sector-by-sector or
      company-by-company.</div>
      <div class="dm-card" style="margin-bottom:0;">🧠 <b>Explain.</b> Each flag is backed by a per-company
      SHAP breakdown showing exactly which indicators — and which year-on-year changes — pushed the score up
      or down.</div>
      <div class="dm-card" style="margin-bottom:0;">📊 <b>Evaluate.</b> The Model Performance page reports
      ROC-AUC, PR-AUC, F1, confusion matrix, and a like-for-like comparison against every RL variant trained
      in this project and the Altman benchmark.</div>
    </div>

    <h3 class="dm-section-gap">Methodology, briefly</h3>
    <div class="dm-panel" style="margin-top:0;">
      <ul style="margin:0; max-width:none;">
        <li><b>Data</b>: quarterly/annual financial ratios for Bursa Malaysia listed companies, plus a
          historical record of PN17/GN3 classification dates (Chapter 3).</li>
        <li><b>State</b>: 16 features — 8 financial ratios (current ratio, quick ratio, cash ratio, ROA, ROE,
          net debt/total capital, asset turnover, Altman Z''-Score) plus their year-on-year deltas, robust
          median/IQR-scaled on the training split.</li>
        <li><b>Agents</b>: a one-step Deep Q-Network and a policy-gradient agent, each also trained as a
          multi-step MDP variant, using a reward function that front-loads credit for early, ahead-of-time
          detection of distress.</li>
        <li><b>Calibration</b>: decision thresholds are chosen on a held-out <b>validation</b> split to
          minimise misclassification cost, then evaluated once on a separate <b>test</b> split — never the
          reverse.</li>
        <li style="margin-bottom:0;"><b>Benchmark</b>: the classical Altman Z''-Score (threshold 1.1),
          computed directly from the same panel, with no RL involved — the yardstick the RL agents are
          measured against.</li>
      </ul>
    </div>

    <h3 class="dm-section-gap">Performance on held-out test data</h3>
    <div class="dm-panel" style="margin-top:0;">
      <div class="dm-table-scroll"><table class="dm-table">
        <thead><tr><th>Method</th><th>Cost</th><th>Recall</th><th>Precision</th></tr></thead>
        <tbody>
          <tr><td>This model (calibrated DQN)</td><td>${card.test_cost}</td><td>${DM.fmtPct(card.test_recall, 1)}</td><td>${DM.fmtPct(card.test_precision, 1)}</td></tr>
          <tr><td>This model, at the Z-Score's recall</td><td>${card.recall_matched_cost}</td><td>${DM.fmtPct(card.recall_matched_recall, 1)}</td><td>${DM.fmtPct(card.recall_matched_precision, 1)}</td></tr>
          <tr><td>Altman Z''-Score (classical benchmark)</td><td>${card.benchmark_altman_cost}</td><td>${DM.fmtPct(card.benchmark_altman_recall, 1)}</td><td>${DM.fmtPct(card.benchmark_altman_precision, 1)}</td></tr>
        </tbody>
      </table></div>
      <p class="dm-caption" style="margin-top:1.1rem;">Cost = 10×(missed distress) + 3×(false alarm), on
      ${card.test_rows.toLocaleString()} held-out company-periods containing ${card.test_positives} genuine
      distress cases. Lower is better. The model beats the classical benchmark on cost at its own operating
      point${beats
        ? ', and at the Z-Score\'s own detection rate too.'
        : `, but NOT at the Z-Score's own detection rate (${card.recall_matched_cost} vs ${card.benchmark_altman_cost})
           — pushed to match that recall, this model currently raises more false alarms than the classical rule
           does. This is disclosed rather than hidden: which operating point to trust is a real, current
           limitation, not settled.`}</p>
      <p class="dm-caption" style="margin-top:.6rem;">See the <b>Performance</b> page in the nav above for the
      full ROC/PR curves, confusion matrix, and cross-agent comparison.</p>
    </div>

    <h3 class="dm-section-gap">What this model cannot do</h3>
    <div class="dm-warn-grid">
      <div class="dm-warn-card">
        <b>⚠️ It misses most distressed companies.</b>
        <span>At its default threshold it catches only ${DM.fmtPct(card.test_recall, 0)} of them. It is a
        triage aid for deciding where to look first, not a substitute for credit analysis.</span>
      </div>
      <div class="dm-warn-card">
        <b>⚠️ Its early-warning ability is unproven.</b>
        <span>Every early flag measured in the current version of this project fell on data the model had
        trained on. One version briefly recorded a genuinely out-of-sample early warning — it did not
        reproduce after the next retrain, and is not repeated here.</span>
      </div>
      <div class="dm-warn-card">
        <b>⚠️ It is trained on very few examples.</b>
        <span>46 distressed company-periods in training. Results have shifted materially across five versions
        of the data pipeline so far, mostly from data corrections rather than model changes — most recently, a
        single company's 3 training rows changed which of the two agents beats the benchmark at matched
        recall.</span>
      </div>
      <div class="dm-warn-card">
        <b>⚠️ It is a backtest, not a live system.</b>
        <span>Never validated on live forward data.</span>
      </div>
      <div class="dm-warn-card" style="grid-column:1/-1;">
        <b>⚠️ Reinforcement learning is not shown to beat conventional classifiers here.</b>
        <span>Benchmarked against five standard supervised models on identical data, features,
        splits and cost function, this dashboard's DQN places third of six on misclassification
        cost and <b>last of every tree-based method on both threshold-free ranking measures</b> —
        which is what a triage tool is actually judged on. Rolling-origin validation across three
        independent train/test boundaries confirms this is not an artefact of one arbitrary split:
        the ranking deficit reproduces at <b>every</b> origin tested, even though the cost ranking
        swings between 2nd and 5th. See the <b>Performance</b> page for the full table. The
        contribution of this project is better read as the end-to-end monitoring and explanation
        system than as evidence that reinforcement learning is the preferable method for distress
        prediction.</span>
      </div>
    </div>

    <h3 class="dm-section-gap">What drives the model overall</h3>
    <div class="dm-panel" style="margin-top:0;">
      <div id="about-gshap" class="dm-chart" style="height:380px;"></div>
      <p class="dm-caption" style="margin-top:1.1rem;">Year-on-year <b>changes</b> in liquidity outrank
      absolute levels — how fast a company is deteriorating carries more signal than where it currently
      stands.</p>
    </div>

    <h3 class="dm-section-gap">Full disclaimer</h3>
    <div class="dm-banner dm-banner-disclaimer" id="about-disclaimer">
      ⚠️ This dashboard is a research prototype produced for an academic capstone project and is <b>not</b>
      financial, investment, credit, or legal advice. It has not been validated on live, forward-looking
      data, is trained on a small number of historical distress examples, and both its recall and precision
      are limited (see Model Performance). Model outputs should be treated as a prompt for further human
      investigation, never as a standalone basis for any investment, lending, trading, or business decision.
      The authors and Sunway Business School accept no liability for decisions made using this tool.
    </div>

    <details class="dm-card dm-section-gap">
      <summary style="cursor:pointer;font-weight:600;">Technical specification (model_card.json)</summary>
      <pre style="background:var(--fill-5);padding:1rem;border-radius:10px;overflow-x:auto;font-size:.8rem;margin:1rem 0 0 0;">${JSON.stringify(card, null, 2)}</pre>
    </details>
  `;

  const g = gshap.slice(0, 10).reverse();
  DM.plot(document.getElementById('about-gshap'), [{
    type: 'bar', orientation: 'h', x: g.map(r => r[1]), y: g.map(r => DM.pretty(r[0])),
  }], { margin: { l: 220, r: 20, t: 10, b: 40 }, yaxis: { automargin: true },
        xaxis: { title: 'Mean |SHAP| across test companies' } });
};
