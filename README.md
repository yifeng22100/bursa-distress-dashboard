# Bursa Distress Monitor — Chapter 4.8 artefact (RQ4)

Interactive monitoring dashboard presenting the calibrated DQN's distress risk scores for 1,065
Bursa Malaysia companies, with a left-sidebar-nav layout and a landing page that orients a
first-time visitor. This is the artefact deliverable answering RQ4.

**A Reinforcement Learning Approach to Corporate Financial Distress Prediction — Feature
Importance Analysis of Bursa Malaysia Listed Companies** (PRJ5158, MsBA Capstone II, Sunway
Business School). Team: Jeremy Choong Ming, Tan Yan Sheng, Tan Yi Feng.

## Run it

```bash
streamlit run dashboard/app.py
```

Opens at http://localhost:8501. Requires `streamlit`, `plotly`, `pandas`, `numpy` (all already
installed in this project's environment).

## Rebuild the data layer

The app reads only pre-computed files in `dashboard/data/`. It does **no** training or scoring,
so every number on screen traces back to one script and to the trained weights in `RL_Model_v1/`.
Regenerate after any model or label change:

```bash
python3 RL_Model_v1/10_build_dashboard_data.py
```

That writes:

| File | Contents |
|---|---|
| `watchlist.csv` | One row per monitored company: risk score, rank, percentile, flag decision, known PN17/GN3 status |
| `watchlist_changes.json` | Companies newly flagged / newly cleared vs the *previous* time this script ran — diffed before the old watchlist.csv is overwritten |
| `company_shap.csv` | Per-company local SHAP values — powers the "why was this company scored this way" panel |
| `sector_risk.csv` | Sector aggregates (mean / median / % flagged / count) |
| `indicator_history.csv` | Raw (unscaled) financial indicators over time, for the trend charts |
| `risk_history.csv` | Risk score over time per company, with train/val/test split membership |
| `model_card.json` | Model config, threshold, and headline test performance — restated so the app cannot drift from the report |
| `global_shap.json` | Global feature-importance ranking |
| `model_metrics.json` | ROC/PR curves, ROC-AUC, PR-AUC, F1, confusion matrix, cross-agent comparison table |
| `model_weights.json` | The calibrated DQN's frozen weights + scaling params, exported as plain JSON arrays — powers the drill-down page's "what-if" slider with a pure-numpy forward pass, so the deployed app never needs a torch install |

## The eight views

0. **Welcome** — the default landing page. Explains what the dashboard is, who it's for
   (investors/analysts, credit & risk teams, students/RL enthusiasts), the single most important
   caveat up front, and a card per remaining view with a one-line question it answers and a button
   that jumps straight there.
1. **Sector risk overview** — aggregates risk to sector level. Defaults to **median** and applies a
   minimum sector size (default 5), because an early version ranked by mean and was dominated by a
   four-company bucket. Companies with no sector (the delisted-firm supplement, 3 of 4 genuinely
   distressed) get their own labelled bucket rather than being dropped.
2. **At-risk company ranking** — the working watchlist, filterable by sector, known status, and a
   free-text name search, with a CSV download of the current view. Shows a plain-language risk band
   next to the raw score, and a "Known status" column so the model's genuine hits and false alarms
   are visible side by side.
3. **Company drill-down** — rank, score, flag decision, a local SHAP explanation (red = pushed risk
   up, green = down), risk score over time against the flag threshold, the underlying indicators, and
   a **"what-if" slider**: nudge the company's most recent ratios and watch the risk score recompute
   live (pure numpy, using the frozen weights in `model_weights.json` — nothing is retrained, nothing
   entered is saved).
4. **Company comparison** — put 2–4 companies side by side: current rank/score/risk band, overlaid
   risk-score-over-time, an overlaid indicator trend, and each company's top SHAP drivers.
5. **Indicator trends** — compare any indicator across companies over time, with actual PN17/GN3
   periods marked.
6. **Model performance** — ROC-AUC, PR-AUC, F1, accuracy, recall, precision; full ROC and
   precision–recall curves plotted against the Altman benchmark's single operating point; a
   confusion matrix; and a cross-agent comparison table (both RL agents, one-step and multi-step,
   against Altman) — all read from `model_metrics.json`, never recomputed in the app.
7. **About & methodology** — project title, team, methodology summary, benchmark comparison, an
   equally prominent statement of what the model cannot do, ideas for future features, and the
   full disclaimer text.

A blue notice banner appears under the disclaimer whenever `watchlist_changes.json` shows
newly-flagged or newly-cleared companies since the last time `10_build_dashboard_data.py` ran —
silent otherwise (first run, or no change).

## Design

Navigation is a persistent **left sidebar** (brand, vertical nav list with a tinted/left-accent
active state, quick stats) rather than a top tab row — closer to how analyst tools like Bloomberg
Terminal or PitchBook are actually laid out, and it scales better now that there are 8 views (the
original top-tab row wrapped to two lines). The visual language inside the main content area keeps
the "consumer app" direction from the author's other two dashboards (hospital-intelligence-my,
malaysia-election-sentiment): bold hero titles with a small uppercase blue "eyebrow" label above
each, colour-tag pills (green/orange/red/gray, dot + caps text) for status/category instead of
plain text, and thin-border cards. Multi-column prose sections (e.g. "Who this is for") are
stacked full-width cards rather than `st.columns`, since 3-wide text columns cramp badly once the
sidebar takes ~300px off the main content width. Font stack tries `"National"` first (HBR's
sans-serif — a paid Klim Type Foundry / Commercial Type font this project holds no licence for, so
almost no viewer will actually have it) then falls back to Inter, a free grotesque with similar
proportions, loaded via Google Fonts. A persistent disclaimer banner sits above the page content on
every view, and a footer cites the project title, team, data sources, and disclaimer.

**Known platform limitation.** Streamlit Community Cloud renders the deployed app inside a
cross-origin iframe and draws its own "Fork / GitHub / menu" toolbar *over* that iframe from the
parent page. The app's CSS/JS has no access to that parent frame — it cannot detect the toolbar's
height, hide it, or move it. Both `.block-container`'s and the sidebar's `padding-top` are set to a
fixed, generously-sized clearance as a guess with margin for safety, not a measurement; if the
masthead or sidebar brand ever looks covered again after a Streamlit Cloud UI change, these are the
values to increase.

**A note on narrow-width bugs.** Moving to a sidebar shrank the main content area by ~300px, which
surfaced several genuine rendering bugs that a wider layout had been masking: `st.metric` values
clipping to an ellipsis (fixed with a capped font-size), a checkbox label wrapping one letter per
line (fixed by rebalancing the filter row's columns), and — the most serious — a horizontal bar
chart's long y-axis labels overflowing Plotly's auto-margin past its column boundary and visually
overlapping the table next to it (fixed by stacking the chart and table vertically instead of
side-by-side). All three were found by actually clicking through every view at the new width, not
assumed fixed from one screenshot.

## Design principles

Three choices follow directly from this project's measured results rather than from UI convention:

- **Risk is always expressed twice** — raw score *and* plain-language band. A raw Q-value means
  nothing to the intended audience; "highest-risk of 1,065" does.
- **Every flag is explainable per company**, not just in aggregate — required for a flag to be
  defensible in a credit file.
- **The false-alarm rate is on the same screen as the results.** The stat band and the "About &
  methodology" table state, live, how many of the currently-flagged companies are genuine vs false alarms,
  and whether the model's recall-matched operating point beats or loses to the Altman benchmark —
  neither of these is hardcoded, both are computed fresh by `RL_Model_v1/10_build_dashboard_data.py`
  each time it runs, after an earlier version's hardcoded copies were found to have silently drifted
  out of sync with the model across two retrains.

Deliberately **not** provided: any composite "risk grade", ranked recommendation, or lending/investment
implication. The model is a triage aid for directing attention, and its measured precision at its
default threshold (currently 57.1%, but recall only 21.1% — see `dashboard/data/model_card.json` for
the live figure) is the strongest claim it supports.

## Regenerating the report screenshots

`dashboard/screenshots/` holds the eight view captures (4_8a–4_8h). Captured headless at 2× scale:

```bash
python3 dashboard/capture_screenshots.py   # selenium + headless Chrome, 1500x1150 @ 2x
```

Note: overwriting these PNGs does **not** update the images already embedded in the .docx — the
document stores its own copies. See the note in the project memory on replacing `word/media/imageN.png`
inside the docx zip.
