DM.renderers.welcome = function (el) {
  const { card, wl } = DM.data;

  const problems = [
    ['🔍', 'Too many companies, too little time.', '1,065 listed companies file every quarter — no realistic way to read every balance sheet by hand.'],
    ['📉', 'Distress hides across ratios, not in one.', 'Deterioration usually shows up as a pattern across several indicators and their year-on-year change, not a single red flag.'],
    ['⚖️', 'Classical tools miss cases too.', "The Altman Z''-Score, the standard benchmark, is useful but far from complete — it misses genuine distress cases of its own."],
    ['🎯', 'Attention is the scarce resource.', "Every false alarm chased down is time not spent on a company that's actually at risk."],
  ];

  const who = [
    ['📈', 'blue', 'Investors & analysts.', 'A triage aid for deciding which of 1,065 companies to look at first — not a buy/sell signal, and not a substitute for reading the actual financials.'],
    ['🏦', 'green', 'Credit & risk teams.', "A second opinion alongside the classical <span style=\"white-space:nowrap;\">Altman Z''-Score</span>, with every flag traceable to the specific indicators that drove it (SHAP), so it can be argued for or against in a credit file."],
    ['🎓', 'purple', 'Students & RL enthusiasts.', "A worked, honestly-reported example of applying reinforcement learning to a real, small, severely imbalanced dataset — including what didn't work and why."],
  ];

  const guide = [
    ['sector', '🏭', 'blue', 'Sectors', 'Where should I start looking?', 'Aggregates risk to the sector level so you can decide which industries warrant attention first.'],
    ['ranking', '📋', 'green', 'Watchlist', 'Show me the working watchlist.', 'Every monitored company ranked by risk score, filterable by sector and status, with a CSV export.'],
    ['drilldown', '🔍', 'orange', 'Drill-down', 'Why is this one company flagged?', "Rank, score, a SHAP explanation of what drove it, risk history, and a live what-if slider."],
    ['comparison', '⚖️', 'purple', 'Compare', 'How does A stack up against B and C?', 'Put 2–4 companies side by side — trajectory, current standing, and what\'s driving each score.'],
    ['trends', '📉', 'teal', 'Trends', 'How has one ratio moved over time?', 'Compare any single financial indicator across companies, with actual distress periods marked.'],
    ['performance', '📊', 'pink', 'Performance', 'Can I trust this model? Show me the numbers.', 'ROC/PR curves, confusion matrix, and a like-for-like comparison against every agent trained.'],
    ['about', '📖', 'red', 'About', 'What is this, exactly, and how was it built?', 'Project background, methodology, limitations, and the full disclaimer.'],
  ];

  const sectors = new Set(wl.map(r => r.sector)).size;

  el.innerHTML = `
    <div class="dm-hero">
      <div class="dm-eyebrow">Bursa Distress Monitor</div>
      <h1>Know which <span class="accent">Bursa Malaysia</span> companies deserve a <span class="accent">second look</span>.</h1>
      <p>A reinforcement-learning early-warning system for corporate financial distress (PN17/GN3
      classification), benchmarked against the classical <span style="white-space:nowrap;">Altman
      Z''-Score</span> — built as a research artefact, not a trading or lending tool.</p>
      <div class="dm-pillrow" id="hero-pills"></div>
    </div>

    <div class="dm-statband">
      <div class="dm-stat-big"><b>${wl.length.toLocaleString()}</b><div class="lbl">Companies</div><div class="cap">Monitored</div></div>
      <div class="dm-stat-big"><b>${sectors}</b><div class="lbl">Sectors</div><div class="cap">Full coverage</div></div>
      <div class="dm-stat-big"><b>${card.watchlist_flagged}</b><div class="lbl">Flagged</div><div class="cap">${card.watchlist_flagged_true} genuine · ${card.watchlist_flagged_false} false alarm</div></div>
      <div class="dm-stat-big"><b>${DM.fmtPct(card.test_recall, 0)}</b><div class="lbl">Recall</div><div class="cap">at calibrated threshold</div></div>
    </div>

    <h3 class="dm-section-gap">Why this matters</h3>
    <p class="dm-caption">The problem a single Altman Z-Score or a spreadsheet full of ratios doesn't solve on its own.</p>
    <div class="dm-card-grid cols-4">
      ${problems.map(([icon, title, desc]) => `
        <div class="dm-card" style="margin-bottom:0;">
          <div style="font-size:1.5rem; margin-bottom:.6rem;">${icon}</div>
          <div style="font-weight:700; margin-bottom:.4rem;">${title}</div>
          <div style="font-size:.88rem; color:var(--ink-soft); line-height:1.5;">${desc}</div>
        </div>
      `).join('')}
    </div>

    <h3 class="dm-section-gap">Who this is for</h3>
    <div class="dm-card-grid cols-3">
      ${who.map(([icon, hue, title, desc]) => `
        <div class="dm-guide-card dm-guide-${hue}" style="cursor:default;">
          <div class="dm-guide-icon">${icon}</div>
          <div class="dm-guide-body">
            <div class="dm-guide-title">${title}</div>
            <div style="font-size:.9rem; color:var(--ink); line-height:1.55;">${desc}</div>
          </div>
        </div>
      `).join('')}
    </div>

    <div style="max-width:820px;margin:0 auto;">
      <div class="dm-banner dm-banner-disclaimer">
        ⚠️ Read this before anything else: this model catches only about ${DM.fmtPct(card.test_recall, 0)}
        of genuinely distressed companies at its default setting, and every flag needs human judgement.
        See the disclaimer below and the full text on the About &amp; methodology page.
      </div>
    </div>

    <h3 class="dm-section-gap">How to use this dashboard</h3>
    <p class="dm-caption">Seven views, each answering a different question. Click through, or use the nav above.</p>
    <div class="dm-guide-grid" id="guide-grid"></div>

    <div class="dm-cta">
      <h3>Have a specific company in mind?</h3>
      <p>Skip straight to its risk score, its SHAP explanation, and a live what-if slider.</p>
      <button class="dm-cta-btn" data-goto="drilldown">Open Drill-down →</button>
    </div>
  `;

  el.querySelector('#hero-pills').innerHTML = guide.map(([id, , , name]) =>
    `<button class="dm-pill-btn" data-goto="${id}">${name}</button>`).join('');
  el.querySelectorAll('#hero-pills button').forEach(btn => {
    btn.addEventListener('click', () => DM.goto(btn.dataset.goto));
  });

  const grid = el.querySelector('#guide-grid');
  grid.innerHTML = guide.map(([id, icon, hue, name, question, desc]) => `
    <div class="dm-guide-card dm-guide-${hue}" data-goto="${id}" role="button" tabindex="0">
      <div class="dm-guide-icon">${icon}</div>
      <div class="dm-guide-body">
        <div class="dm-guide-title">${name}</div>
        <p class="dm-guide-question">"${question}"</p>
        <p class="dm-guide-desc">${desc}</p>
        <span class="dm-guide-link">Open ${name} <span class="arrow">→</span></span>
      </div>
    </div>
  `).join('');
  grid.querySelectorAll('.dm-guide-card').forEach(c => {
    c.addEventListener('click', () => DM.goto(c.dataset.goto));
    c.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); DM.goto(c.dataset.goto); }
    });
  });

  el.querySelector('.dm-cta-btn').addEventListener('click', (e) => DM.goto(e.currentTarget.dataset.goto));
};
