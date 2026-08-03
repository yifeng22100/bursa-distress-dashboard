# Bursa Distress Monitor — Chapter 4.8 artefact (RQ4)

Interactive monitoring dashboard presenting the calibrated DQN's distress risk scores for
1,065 Bursa Malaysia companies. This is the artefact deliverable answering RQ4.

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
| `company_shap.csv` | Per-company local SHAP values — powers the "why was this company scored this way" panel |
| `sector_risk.csv` | Sector aggregates (mean / median / % flagged / count) |
| `indicator_history.csv` | Raw (unscaled) financial indicators over time, for the trend charts |
| `risk_history.csv` | Risk score over time per company, with train/val/test split membership |
| `model_card.json` | Model config, threshold, and headline test performance — restated so the app cannot drift from the report |
| `global_shap.json` | Global feature-importance ranking |

## The five views

1. **Sector risk overview** — aggregates risk to sector level. Defaults to **median** and applies a
   minimum sector size (default 5), because an early version ranked by mean and was dominated by a
   four-company bucket. Companies with no sector (the delisted-firm supplement, 3 of 4 genuinely
   distressed) get their own labelled bucket rather than being dropped.
2. **At-risk company ranking** — the working watchlist, filterable by sector and known status.
   Shows a plain-language risk band next to the raw score, and a "Known status" column so the
   model's genuine hits and false alarms are visible side by side.
3. **Company drill-down** — rank, score, flag decision, a local SHAP explanation (red = pushed risk
   up, green = down), risk score over time against the flag threshold, and the underlying indicators.
4. **Indicator trends** — compare any indicator across companies over time, with actual PN17/GN3
   periods marked.
5. **About this model** — benchmark comparison **and** an equally prominent statement of what the
   model cannot do.

## Design principles

Three choices follow directly from this project's measured results rather than from UI convention:

- **Risk is always expressed twice** — raw score *and* plain-language band. A raw Q-value means
  nothing to the intended audience; "highest-risk of 1,065" does.
- **Every flag is explainable per company**, not just in aggregate — required for a flag to be
  defensible in a credit file.
- **The false-alarm rate is on the same screen as the results.** The sidebar and the "About this
  model" table state, live, how many of the currently-flagged companies are genuine vs false alarms,
  and whether the model's recall-matched operating point beats or loses to the Altman benchmark —
  neither of these is hardcoded, both are computed fresh by `RL_Model_v1/10_build_dashboard_data.py`
  each time it runs, after an earlier version's hardcoded copies were found to have silently drifted
  out of sync with the model across two retrains.

Deliberately **not** provided: any composite "risk grade", ranked recommendation, or lending/investment
implication. The model is a triage aid for directing attention, and its measured precision at its
default threshold (currently 57.1%, but recall only 21.1% — see `dashboard/data/model_card.json` for
the live figure) is the strongest claim it supports.

## Regenerating the report screenshots

`dashboard/screenshots/` holds Figures 4.5–4.9. They were captured headless at 2× scale:

```bash
python3 /tmp/shot.py   # selenium + headless Chrome, 1500x1150 @ 2x
```

Note: overwriting these PNGs does **not** update the images already embedded in the .docx — the
document stores its own copies. See the note in the project memory on replacing `word/media/imageN.png`
inside the docx zip.
