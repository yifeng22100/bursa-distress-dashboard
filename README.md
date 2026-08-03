# Bursa Distress Monitor — Chapter 4.8 artefact (RQ4)

Interactive monitoring dashboard presenting the calibrated DQN's distress risk scores for 1,065
Bursa Malaysia companies. This is the artefact deliverable answering RQ4.

**A Reinforcement Learning Approach to Corporate Financial Distress Prediction — Feature
Importance Analysis of Bursa Malaysia Listed Companies** (PRJ5158, MsBA Capstone II, Sunway
Business School). Team: Jeremy Choong Ming, Tan Yan Sheng, Tan Yi Feng.

**Two implementations live in this repo:**

- **`dashboard/docs/`** — a plain HTML/CSS/JS static site, deployed via GitHub Pages. **This is the
  current, primary version.**
- **`dashboard/app.py`** — the original Streamlit app, kept working and deployed on Streamlit
  Community Cloud, but superseded as the primary deliverable (see "Why the static site" below).

Both read the exact same generated data (`RL_Model_v1/10_build_dashboard_data.py` writes to both
`dashboard/data/` and `dashboard/docs/data/` in one run — see that script's final section), so
neither can silently drift out of sync with the other or with the report.

## Run the static site

```bash
cd dashboard/docs && python3 -m http.server 8123
```

Open http://localhost:8123/ — a server is required (not just opening `index.html` directly)
because the page `fetch()`s its data files, which browsers block over `file://`. No npm, no build
step, no dependencies beyond two CDN-loaded libraries (Plotly.js for charts, PapaParse for CSV
parsing).

**Cache-busting note:** every asset in `index.html` is loaded with a `?v=N` query string. Bump N
on every one of these whenever you edit `css/style.css` or any `js/` file — otherwise a browser
that already has the old file cached (including this project's own dev-loop) will keep serving it
after a hard reload, since `location.reload(true)`'s cache-bypass argument is deprecated and
ignored by modern browsers. This exact issue caused a real, hard-to-diagnose bug during
development: a CSS fix appeared not to work for several reload attempts, purely because the
browser was still executing the pre-fix stylesheet.

## Run the (legacy) Streamlit app

```bash
streamlit run dashboard/app.py
```

Opens at http://localhost:8501. Requires `streamlit`, `plotly`, `pandas`, `numpy`.

## Rebuild the data layer

Neither app does any training or scoring itself — both only read pre-computed files, so every
number on screen traces back to one script and to the trained weights in `RL_Model_v1/`.
Regenerate after any model or label change:

```bash
python3 RL_Model_v1/10_build_dashboard_data.py
```

That writes each of the following to **both** `dashboard/data/` and `dashboard/docs/data/`:

| File | Contents |
|---|---|
| `watchlist.csv` | One row per monitored company: risk score, rank, percentile, flag decision, known PN17/GN3 status |
| `watchlist_changes.json` | Companies newly flagged / newly cleared vs the *previous* time this script ran — diffed before the old watchlist.csv is overwritten |
| `company_shap.csv` | Per-company local SHAP values — powers the "why was this company scored this way" panel |
| `sector_risk.csv` | Sector aggregates (mean / median / % flagged / count) |
| `indicator_history.csv` | Raw (unscaled) financial indicators over time, for the trend charts |
| `risk_history.csv` | Risk score over time per company, with train/val/test split membership |
| `model_card.json` | Model config, threshold, and headline test performance — computed live, never hardcoded |
| `global_shap.json` | Global feature-importance ranking |
| `model_metrics.json` | ROC/PR curves, ROC-AUC, PR-AUC, F1, confusion matrix, cross-agent comparison table |
| `model_weights.json` | The calibrated DQN's frozen weights + scaling params, exported as plain JSON arrays — powers the drill-down page's "what-if" slider with a pure-math forward pass (numpy in Streamlit, plain JS in the static site), so neither app needs a torch install |

## Static site file layout

```
dashboard/docs/
  index.html          shell: header nav, disclaimer/alert banners, one <main> with 8 view sections
  css/style.css        the whole design system (see "Design" below)
  js/data.js            fetch()+PapaParse loader for every CSV/JSON on load
  js/nav.js             view switching, active-nav-item state, URL hash routing (#sector, #about, ...)
  js/components.js       the chip-multiselect (search + chips) used by ranking/comparison/trends
  js/charts.js           shared Plotly.js layout/styling helpers
  js/whatif.js           the frozen DQN's forward pass, ported to plain JS arrays (no numpy needed)
  js/views/*.js          one render(container) function per view, registered into DM.renderers
  data/                  the static-site mirror of dashboard/data/ (see "Rebuild the data layer")
```

## The eight views

0. **Home** — the landing page. A centered hero (eyebrow, headline, subtitle, quick-jump pills)
   and a full-width stat band, then "who this is for" and a card per other view with a one-line
   question it answers and a button that jumps straight there.
1. **Sectors** — aggregates risk to sector level. Defaults to **median** and applies a minimum
   sector size (default 5), because an early version ranked by mean and was dominated by a
   four-company bucket. Companies with no sector (the delisted-firm supplement, 3 of 4 genuinely
   distressed) get their own labelled bucket rather than being dropped.
2. **Watchlist** — the working watchlist, filterable by sector, known status, and a free-text name
   search, with a CSV download of the current view (client-side blob download, no server). Shows a
   plain-language risk band next to the raw score, and a "Known status" column so the model's
   genuine hits and false alarms are visible side by side.
3. **Drill-down** — rank, score, flag decision, a local SHAP explanation (red = pushed risk up,
   green = down), risk score over time against the flag threshold, the underlying indicators, and
   a **"what-if" slider**: nudge the company's most recent ratios and watch the risk score
   recompute live, entirely client-side — nothing is retrained, nothing entered is saved.
4. **Compare** — put 2–4 companies side by side: current rank/score/risk band, overlaid
   risk-score-over-time, an overlaid indicator trend, and each company's top SHAP drivers.
5. **Trends** — compare any indicator across companies over time, with actual PN17/GN3 periods
   marked.
6. **Performance** — ROC-AUC, PR-AUC, F1, accuracy, recall, precision; full ROC and
   precision–recall curves plotted against the Altman benchmark's single operating point; a
   confusion matrix; and a cross-agent comparison table (both RL agents, one-step and multi-step,
   against Altman) — all read from `model_metrics.json`, never recomputed in the app.
7. **About** — project title, team, methodology summary, benchmark comparison, an equally
   prominent statement of what the model cannot do, ideas for future features, and the full
   disclaimer text.

A blue notice banner appears under the disclaimer whenever `watchlist_changes.json` shows
newly-flagged or newly-cleared companies since the last time `10_build_dashboard_data.py` ran —
silent otherwise (first run, or no change).

## Design

Modelled directly on two references, with exact values pulled from the live pages via
`getComputedStyle()` rather than approximated:

- **developer.apple.com/design/resources** and the linked Apple macOS UI Kit Sketch file
  (Color Variables page) — font stack leads with `-apple-system, BlinkMacSystemFont` (renders
  real San Francisco on Apple devices, no licence needed), and dividers/hover states use Apple's
  own documented light-mode "Fill" overlay opacities (black at 10/8/5/3/2%).
- **hospital-intelligence-my** (the author's other project) — accent blue `#0071E3` (Apple's
  marketing-site blue, distinct from the HIG systemBlue `#007AFF` — confirmed by inspecting the
  live page, not assumed), a top nav bar with plain-text links (16px/400 weight, blue + underline
  on the active item) rather than a sidebar, a centered hero (H1 at 56px/700/-1.4px tracking,
  eyebrow at 12px/600/+1.44px tracking uppercase), a full-width light-gray (`#F5F5F7`) stat band
  under the hero, pill-shaped filter chips (fully round, `#D2D2D7` border), and thin-border cards
  with **no** drop shadow.

## Why the static site

An earlier version of this dashboard was built entirely in Streamlit. Several rounds of CSS work
there kept running into the same wall: Streamlit Community Cloud renders the app inside a
cross-origin iframe and draws its own toolbar *over* it from the parent page (undetectable and
unfixable from inside the app); `st.dataframe` is a canvas-rendered widget that ignores CSS
entirely; native widgets (sliders, radios, checkboxes) only take colour from one theme config
file, not arbitrary CSS; and the column-based layout has no real flexbox/grid control. Concretely,
this produced: a masthead hidden under Streamlit Cloud's own toolbar, a checkbox label that
wrapped one letter per line once the layout narrowed, `st.metric` values clipping to an ellipsis,
and a bar chart's long labels overflowing into the column next to it. All were fixed at the time,
but each fix was a workaround for a platform constraint, not a real solution — and the visual
result still couldn't fully match the target reference sites, which are themselves plain static
pages with full CSS control.

The migration was unusually cheap because the model layer was already fully decoupled: the
what-if slider already ran on plain matrix math (not live Python inference) against frozen weights
exported to `model_weights.json`, so porting it to JS was mechanical — verified against the
original torch model's output to 5+ decimal places before being wired into the UI (`DM.whatifSelfTest()`
in `js/whatif.js`, which runs automatically on every page load and logs a console error if it ever
drifts).

The old `app.py` remains as-is for anyone who wants to compare the two, or in case the static
site's GitHub Pages hosting is ever unavailable.

## Design principles

Three choices follow directly from this project's measured results rather than from UI convention:

- **Risk is always expressed twice** — raw score *and* plain-language band. A raw Q-value means
  nothing to the intended audience; "highest-risk of 1,065" does.
- **Every flag is explainable per company**, not just in aggregate — required for a flag to be
  defensible in a credit file.
- **The false-alarm rate is on the same screen as the results.** The stat band and the About page
  state, live, how many of the currently-flagged companies are genuine vs false alarms, and
  whether the model's recall-matched operating point beats or loses to the Altman benchmark —
  neither of these is hardcoded, both are computed fresh by `RL_Model_v1/10_build_dashboard_data.py`
  each time it runs, after an earlier version's hardcoded copies were found to have silently
  drifted out of sync with the model across two retrains.

Deliberately **not** provided: any composite "risk grade", ranked recommendation, or lending/investment
implication. The model is a triage aid for directing attention, and its measured precision at its
default threshold (currently 57.1%, but recall only 21.1% — see `dashboard/data/model_card.json` for
the live figure) is the strongest claim it supports.

## Regenerating the report screenshots

`dashboard/screenshots/` holds the eight view captures (4_8a–4_8h), now captured from the static
site. Serve it first, then:

```bash
cd dashboard/docs && python3 -m http.server 8123 &
python3 dashboard/capture_screenshots.py   # selenium + headless Chrome, 1500x1150 @ 2x
```

Note: overwriting these PNGs does **not** update the images already embedded in the .docx — the
document stores its own copies. See the note in the project memory on replacing `word/media/imageN.png`
inside the docx zip.

## Deploying to GitHub Pages

In the GitHub repo's Settings → Pages, set the source to the `main` branch, `/docs` folder (not
`/root`), and save. GitHub serves `dashboard/docs/index.html` at
`https://<username>.github.io/<repo-name>/` a minute or two after the next push.
