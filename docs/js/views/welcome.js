DM.renderers.welcome = function (el) {
  const { card, wl } = DM.data;

  const who = [
    ['📈', 'Investors & analysts.', 'A triage aid for deciding which of 1,065 companies to look at first — not a buy/sell signal, and not a substitute for reading the actual financials.'],
    ['🏦', 'Credit & risk teams.', "A second opinion alongside the Altman Z''-Score, with every flag traceable to the specific indicators that drove it (SHAP), so it can be argued for or against in a credit file."],
    ['🎓', 'Students & RL enthusiasts.', "A worked, honestly-reported example of applying reinforcement learning to a real, small, severely imbalanced dataset — including what didn't work and why."],
  ];

  const guide = [
    ['sector', '🏭', 'Sectors', 'Where should I start looking?', 'Aggregates risk to the sector level so you can decide which industries warrant attention first.'],
    ['ranking', '📋', 'Watchlist', 'Show me the working watchlist.', 'Every monitored company ranked by risk score, filterable by sector and status, with a CSV export.'],
    ['drilldown', '🔍', 'Drill-down', 'Why is this one company flagged?', "Rank, score, a SHAP explanation of what drove it, risk history, and a live what-if slider."],
    ['comparison', '⚖️', 'Compare', 'How does A stack up against B and C?', 'Put 2–4 companies side by side — trajectory, current standing, and what\'s driving each score.'],
    ['trends', '📉', 'Trends', 'How has one ratio moved over time?', 'Compare any single financial indicator across companies, with actual distress periods marked.'],
    ['performance', '📊', 'Performance', 'Can I trust this model? Show me the numbers.', 'ROC/PR curves, confusion matrix, and a like-for-like comparison against every agent trained.'],
    ['about', '📖', 'About', 'What is this, exactly, and how was it built?', 'Project background, methodology, limitations, and the full disclaimer.'],
  ];

  const sectors = new Set(wl.map(r => r.sector)).size;

  el.innerHTML = `
    <div class="dm-hero">
      <div class="dm-eyebrow">Bursa Distress Monitor</div>
      <h1>Know which Bursa Malaysia companies deserve a second look.</h1>
      <p>A reinforcement-learning early-warning system for corporate financial distress (PN17/GN3
      classification), benchmarked against the classical Altman&nbsp;Z''-Score — built as a research
      artefact, not a trading or lending tool.</p>
      <div class="dm-pillrow" id="hero-pills"></div>
    </div>

    <div class="dm-statband">
      <div class="dm-stat-big"><b>${wl.length.toLocaleString()}</b><div class="lbl">Companies</div><div class="cap">Monitored</div></div>
      <div class="dm-stat-big"><b>${sectors}</b><div class="lbl">Sectors</div><div class="cap">Full coverage</div></div>
      <div class="dm-stat-big"><b>${card.watchlist_flagged}</b><div class="lbl">Flagged</div><div class="cap">${card.watchlist_flagged_true} genuine · ${card.watchlist_flagged_false} false alarm</div></div>
      <div class="dm-stat-big"><b>${DM.fmtPct(card.test_recall, 0)}</b><div class="lbl">Recall</div><div class="cap">at calibrated threshold</div></div>
    </div>

    <div style="max-width:820px;margin:0 auto;">
      <h3 class="dm-section-gap">Who this is for</h3>
      ${who.map(([icon, title, desc]) => `
        <div class="dm-card">${icon} <b>${title}</b> ${desc}</div>
      `).join('')}

      <div class="dm-banner dm-banner-disclaimer">
        ⚠️ Read this before anything else: this model catches only about ${DM.fmtPct(card.test_recall, 0)}
        of genuinely distressed companies at its default setting, and every flag needs human judgement.
        See the disclaimer below and the full text on the About &amp; methodology page.
      </div>
    </div>

    <h3 class="dm-section-gap">How to use this dashboard</h3>
    <p class="dm-caption">Seven views, each answering a different question. Click through, or use the nav above.</p>
    <div class="dm-card-grid cols-2" id="guide-grid"></div>
  `;

  el.querySelector('#hero-pills').innerHTML = guide.map(([id, , name]) =>
    `<button class="dm-pill-btn" data-goto="${id}">${name}</button>`).join('');
  el.querySelectorAll('#hero-pills button').forEach(btn => {
    btn.addEventListener('click', () => DM.goto(btn.dataset.goto));
  });

  const grid = el.querySelector('#guide-grid');
  grid.innerHTML = guide.map(([id, icon, name, question, desc]) => `
    <div>
      <div class="dm-card">
        <span style="font-size:1.3rem;">${icon}</span> <b>${name}</b><br>
        <span style="color:var(--ink-soft);font-style:italic;">"${question}"</span><br><br>
        ${desc}
      </div>
      <button class="dm-btn" data-goto="${id}">Open ${name} →</button>
    </div>
  `).join('');
  grid.querySelectorAll('button[data-goto]').forEach(btn => {
    btn.addEventListener('click', () => DM.goto(btn.dataset.goto));
  });
};
