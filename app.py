"""
Bursa Malaysia Corporate Distress Monitor
Capstone II (PRJ5158) — Chapter 4.8 artefact, answering RQ4.

Reads only the pre-computed files in dashboard/data/ (built by RL_Model_v1/10_build_dashboard_data.py).
No training or scoring happens here, so every number on screen traces back to that script and to the
trained weights in RL_Model_v1/.

Run:  streamlit run dashboard/app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import json, os
import plotly.express as px
import plotly.graph_objects as go

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

PROJECT_TITLE = ("A Reinforcement Learning Approach to Corporate Financial Distress Prediction — "
                  "Feature Importance Analysis of Bursa Malaysia Listed Companies")
PROJECT_CODE = "PRJ5158 · MsBA Capstone II · Sunway Business School"
TEAM = sorted(["Tan Yi Feng", "Jeremy Choong Ming", "Tan Yan Sheng"])

st.set_page_config(page_title="Bursa Distress Monitor", page_icon="⚠️", layout="wide",
                    initial_sidebar_state="collapsed")

# ---------------------------------------------------------------- design system
# Font: Google Sans isn't distributable as a web font (proprietary to Google products), so it's
# listed first for the rare viewer who has it installed system-wide (ChromeOS/Android), then
# falls back to Roboto — Google's actual open-source sister typeface, loaded from Google Fonts,
# which is what almost every viewer will actually see.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&display=swap');
:root{
  --bg:#FFFFFF; --card:#FFFFFF; --ink:#1D1D1F; --ink-soft:#6E6E73;
  --line:#E5E5EA; --blue:#0071E3; --red:#FF3B30; --orange:#FF9500;
  --green:#34C759; --gold:#B8860B;
  --primary-color:#0071E3;
}
html, body, [class*="css"]{
  font-family:"Google Sans","Google Sans Text",Roboto,-apple-system,BlinkMacSystemFont,
              "Helvetica Neue",Arial,sans-serif !important;
  color:var(--ink);
}
.stApp{ background:var(--bg); }
.block-container{ max-width:1200px; padding-top:0 !important; }

/* ---- masthead + nav: one continuous flat bar, plain-text underline nav — matches the
   author's other dashboards (hospital-intelligence-my, malaysia-election-sentiment) rather
   than the boxed-pill segmented control used in the first draft ---- */
.dm-masthead{
  background:var(--card); border-bottom:1px solid var(--line);
  margin:0 -1rem 0 -1rem; padding:1.1rem 1.6rem .7rem 1.6rem;
}
.dm-header-row{ display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:.9rem 1.6rem;}
.dm-brand{ font-size:1.4rem; font-weight:900; letter-spacing:-0.01em; color:var(--ink); }
.dm-brand span{ color:var(--blue); }
.dm-tagline{ font-size:.8rem; color:var(--ink-soft); margin-top:.1rem; }
.dm-statband{
  background:#F7F7F8; border-bottom:1px solid var(--line);
  margin:0 -1rem 1.4rem -1rem; padding:.85rem 1.6rem; display:flex; align-items:center;
  justify-content:space-between; flex-wrap:wrap; gap:.7rem 1.6rem;
}
.dm-header-stats{ display:flex; align-items:center; gap:1.4rem; }
.dm-stat{ text-align:right; line-height:1.15; }
.dm-stat b{ font-size:1.5rem; font-weight:700; color:var(--ink); display:block; }
.dm-stat span{ font-size:.72rem; color:var(--ink-soft); }
.dm-stat-note{ max-width:260px; font-size:.72rem; color:var(--ink-soft); line-height:1.35; text-align:left; }

/* ---- eyebrow + hero page title, mirroring the author's other dashboards ---- */
.dm-eyebrow{
  font-size:.72rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
  color:var(--blue); margin-bottom:.25rem;
}
.dm-pagetitle{
  font-size:2.05rem; font-weight:800; letter-spacing:-0.02em; margin:0 0 .3rem 0; color:var(--ink);
  line-height:1.15;
}

/* ---- colour-tag pills (status/category), same idiom as the author's other projects ---- */
.dm-tag{
  display:inline-flex; align-items:center; gap:.32rem; padding:.2rem .62rem; border-radius:999px;
  font-size:.72rem; font-weight:700; letter-spacing:.02em; border:1px solid; margin-right:.4rem;
  white-space:nowrap;
}
.dm-tag-dot{ width:6px; height:6px; border-radius:50%; background:currentColor; display:inline-block; }
.dm-tag-green{ background:#E8F8ED; color:#1E7B34; border-color:#BEEACB; }
.dm-tag-red{ background:#FDEBEA; color:#C41E1E; border-color:#F8C9C6; }
.dm-tag-orange{ background:#FFF3E0; color:#B25E00; border-color:#FFDDA8; }
.dm-tag-gray{ background:#F0F0F2; color:#6E6E73; border-color:#E5E5EA; }
.dm-tag-blue{ background:#EAF2FE; color:#0058C6; border-color:#C7DFFB; }

/* ---- cards / callouts ---- */
.dm-card{
  background:var(--card); border-radius:16px; border:1px solid var(--line);
  box-shadow:0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
  padding:1.1rem 1.3rem; margin-bottom:1rem;
}
.dm-banner{
  border-radius:14px; padding:.75rem 1.1rem; font-size:.9rem; line-height:1.45;
  margin-bottom:1.1rem; border:1px solid;
}
.dm-banner-disclaimer{ background:#FFF7ED; border-color:#FFE0B2; color:#7A4A00; }
.dm-pill{
  display:inline-block; padding:.15rem .65rem; border-radius:999px; font-size:.76rem;
  font-weight:600; margin-right:.35rem;
}

/* ---- footer ---- */
.dm-footer{
  margin-top:2.5rem; padding-top:1.4rem; border-top:1px solid var(--line);
  color:var(--ink-soft); font-size:.82rem; line-height:1.6;
}
.dm-footer b{ color:var(--ink); }

/* ---- metrics polish ---- */
[data-testid="stMetric"]{
  background:var(--card); border:1px solid var(--line); border-radius:14px;
  padding:.7rem .9rem; box-shadow:0 1px 3px rgba(0,0,0,.04);
}
[data-testid="stMetricLabel"]{ color:var(--ink-soft); }

/* ---- dataframe / table corners ---- */
[data-testid="stDataFrame"]{ border-radius:14px; overflow:hidden; border:1px solid var(--line); }

/* ---- top nav: plain-text underline links, not boxed pills — matches the author's other
   dashboards, whose nav bars are flat text menus with an underline on the active item ---- */
div[data-testid="stRadio"]{
  margin:0 -1rem 0 -1rem; padding:0 1.6rem; border-bottom:1px solid var(--line); background:var(--card);
}
div[role="radiogroup"]{ gap:0; flex-wrap:wrap; }
div[role="radiogroup"] label{
  background:none; border-radius:0; padding:.75rem .1rem; margin:0 1.3rem 0 0;
  border-bottom:2px solid transparent; transition:color .15s ease, border-color .15s ease;
  color:var(--ink-soft); font-weight:500;
}
div[role="radiogroup"] label:hover{ background:none; color:var(--ink); }
div[role="radiogroup"] label:has(input:checked){
  color:var(--blue); font-weight:700; border-bottom-color:var(--blue);
}
div[role="radiogroup"] label > div:first-child{ display:none; }

/* ---- buttons ---- */
.stButton>button, .stDownloadButton>button{
  border-radius:10px; border:1px solid var(--line); background:var(--card);
}
.stButton>button:hover, .stDownloadButton>button:hover{ border-color:var(--blue); color:var(--blue); }

h1,h2,h3{ letter-spacing:-0.01em; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- data
@st.cache_data
def load():
    wl = pd.read_csv(f"{DATA}/watchlist.csv")
    sec = pd.read_csv(f"{DATA}/sector_risk.csv")
    hist = pd.read_csv(f"{DATA}/indicator_history.csv")
    rh = pd.read_csv(f"{DATA}/risk_history.csv")
    shap_df = pd.read_csv(f"{DATA}/company_shap.csv")
    card = json.load(open(f"{DATA}/model_card.json"))
    gshap = json.load(open(f"{DATA}/global_shap.json"))
    metrics = json.load(open(f"{DATA}/model_metrics.json"))
    return wl, sec, hist, rh, shap_df, card, gshap, metrics

wl, sec, hist, rh, shap_df, card, gshap, metrics = load()

PRETTY = {
    'current_ratio': 'Current Ratio', 'quick_ratio': 'Quick Ratio', 'cash_ratio': 'Cash Ratio',
    'roa': 'Return on Assets', 'roe': 'Return on Equity',
    'net_debt_to_total_capital': 'Net Debt / Total Capital',
    'asset_turnover': 'Asset Turnover', 'zscore_nonmanufacturing': "Altman Z''-Score",
}
def pretty(f):
    if f.endswith('_delta'):
        return PRETTY.get(f[:-6], f[:-6]) + " — year-on-year change"
    return PRETTY.get(f, f)

def band(pct):
    """Translate a percentile into words. The raw Q-value means nothing to a non-technical user."""
    if pct >= 99.0: return "Elevated", "#FF3B30"
    if pct >= 95.0: return "Watch", "#FF9500"
    if pct >= 80.0: return "Moderate", "#B8860B"
    return "Low", "#34C759"

def tag(text, color="gray"):
    return f'<span class="dm-tag dm-tag-{color}"><span class="dm-tag-dot"></span>{text}</span>'

def page_header(eyebrow, title, caption=None):
    st.markdown(f'<div class="dm-eyebrow">{eyebrow}</div><div class="dm-pagetitle">{title}</div>',
                unsafe_allow_html=True)
    if caption:
        st.caption(caption)

# ---------------------------------------------------------------- masthead + stat band
# Everything lives in one in-flow block (no sidebar, nothing sticky) so it never fights
# Streamlit's own toolbar/header chrome for the same space. Only bleeds left/right, never up.
st.markdown(f"""
<div class="dm-masthead">
  <div class="dm-header-row">
    <div>
      <div class="dm-brand">⚠️ Bursa <span>Distress</span> Monitor</div>
      <div class="dm-tagline">RL early-warning prototype for PN17/GN3 classification · Chapter 4.8 artefact (RQ4)
      · {PROJECT_CODE}</div>
    </div>
  </div>
</div>
<div class="dm-statband">
  <div class="dm-header-stats">
    <div class="dm-stat"><b>{len(wl):,}</b><span>companies monitored</span></div>
    <div class="dm-stat"><b>{card['watchlist_flagged']}</b><span>currently flagged</span></div>
  </div>
  <div class="dm-stat-note">
    {tag(f"{card['watchlist_flagged_true']} genuine", "green")}{tag(f"{card['watchlist_flagged_false']} false alarms", "orange")}
    flags are a prompt to look, not a conclusion.
  </div>
</div>
""", unsafe_allow_html=True)

NAV = ["Sector risk overview", "At-risk company ranking", "Company drill-down",
       "Indicator trends", "Model performance", "About & methodology"]
view = st.radio("Navigate", NAV, horizontal=True, label_visibility="collapsed")

st.markdown(f"""
<div class="dm-banner dm-banner-disclaimer">
  ⚠️ <b>Disclaimer.</b> This is a student research prototype, not financial or investment advice.
  It flags companies for further human review and misses most distressed companies at its default
  threshold (recall {card['test_recall']:.0%} on held-out test data). Do not use it, alone or in
  combination with other information, to make investment, lending, or credit decisions.
</div>
""", unsafe_allow_html=True)

# ================================================================ 1. SECTOR
if view == "Sector risk overview":
    page_header("Risk monitoring", "Sector risk overview",
        "Model risk score aggregated by sector, across each company's most recent reported period. "
        "Use this to decide where to look first — not as a verdict on any sector.")

    o1, o2 = st.columns([2, 3])
    with o1:
        metric = st.selectbox(
            "Rank sectors by",
            ['median_risk', 'mean_risk', 'flagged_pct'],
            format_func=lambda m: {'median_risk': 'Median risk score (recommended)',
                                   'mean_risk': 'Mean risk score',
                                   'flagged_pct': '% of companies flagged'}[m])
    with o2:
        min_n = st.slider(
            "Minimum companies in sector", 1, 20, 5,
            help="Sectors with only a handful of companies produce very noisy averages. "
                 "Raising this hides them.")

    view_sec = sec[sec['companies'] >= min_n].copy()
    hidden = sec[sec['companies'] < min_n]

    c1, c2 = st.columns([3, 2])
    with c1:
        top = view_sec.nlargest(15, metric).sort_values(metric)
        lbl = {'median_risk': 'Median risk score', 'mean_risk': 'Mean risk score',
               'flagged_pct': '% of companies flagged'}[metric]
        fig = px.bar(
            top, x=metric, y='sector', orientation='h',
            color=metric, color_continuous_scale=['#34C759', '#B8860B', '#FF9500', '#FF3B30'],
            labels={metric: lbl, 'sector': ''},
            hover_data={'companies': True, 'flagged': True, 'currently_distressed': True, metric: ':.2f'},
        )
        fig.update_layout(height=520, coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0),
                           plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Highest-risk sectors")
        short = {'median_risk': 'Median', 'mean_risk': 'Mean', 'flagged_pct': '% flagged'}[metric]
        show = view_sec.nlargest(15, metric)[['sector', 'companies', metric, 'currently_distressed']]
        show.columns = ['Sector', 'Cos.', short, 'PN17']
        st.dataframe(show.style.format({short: '{:.2f}'}), hide_index=True,
                     use_container_width=True, height=520)

    st.info(
        f"**Why median, and why a minimum size.** A sector's *mean* risk is easily dominated by one or two extreme "
        f"companies, and a sector holding three firms can top any ranking by chance — so the default view uses the "
        f"median and hides sectors with fewer than {min_n} companies "
        f"({len(hidden)} sector{'s' if len(hidden) != 1 else ''} hidden at this setting). Switch the controls above "
        f"to see the alternatives; the 'Cos.' column is shown so sector size is always visible."
    )
    n_unc = int(sec.loc[sec['sector'].str.startswith('(not classified'), 'companies'].sum() or 0)
    if n_unc:
        d = int(sec.loc[sec['sector'].str.startswith('(not classified'), 'currently_distressed'].sum())
        st.warning(
            f"**{n_unc} companies carry no sector classification** and appear as their own bucket. These are the "
            f"delisted-firm supplement records (Chapter 3), and {d} of them are genuinely distressed — so excluding "
            "them, which earlier drafts of this analysis did, would make the sector picture look better than it is."
        )

# ================================================================ 2. RANKING
elif view == "At-risk company ranking":
    page_header("Company watchlist", "At-risk company ranking",
        "Every monitored company, ranked by model risk score on its most recent reported period.")

    c1, c2, c3, c4 = st.columns([2, 2, 1.4, 1])
    with c1:
        secs = st.multiselect("Filter by sector", sorted(wl['sector'].unique()))
    with c2:
        stat = st.multiselect("Filter by known status", sorted(wl['known_status'].unique()))
    with c3:
        search = st.text_input("Search company name", placeholder="e.g. Sentoria")
    with c4:
        only_flagged = st.checkbox("Flagged only", value=False)

    v = wl.copy()
    if secs: v = v[v['sector'].isin(secs)]
    if stat: v = v[v['known_status'].isin(stat)]
    if search: v = v[v['company_name'].str.contains(search, case=False, na=False)]
    if only_flagged: v = v[v['flagged']]

    n = st.slider("Show top N", 10, 200, 25, step=5)
    v = v.nsmallest(n, 'rank')

    v['Risk band'] = v['risk_percentile'].apply(lambda p: band(p)[0])
    disp = v[['rank', 'company_name', 'sector', 'period_end',
              'risk_score', 'Risk band', 'flagged', 'known_status']].copy()
    disp.columns = ['#', 'Company', 'Sector', 'Period end',
                    'Risk score', 'Risk band', 'Flagged', 'Known status']
    st.dataframe(
        disp.style.format({'Risk score': '{:.2f}'}),
        hide_index=True, use_container_width=True, height=min(620, 40 + 35 * len(disp)),
    )
    st.download_button(
        "⬇ Download this view as CSV", disp.to_csv(index=False).encode(),
        file_name="bursa_distress_watchlist.csv", mime="text/csv",
    )

    st.markdown(
        f"**How to read the 'Flagged' column.** A company is flagged when its risk score exceeds the model's "
        f"calibrated decision threshold ({card['threshold']:.2f}), chosen on validation data to minimise the "
        f"cost of mistakes — never on the test data used to measure performance. On the held-out test set this "
        f"threshold caught {card['test_recall']:.0%} of genuinely distressed companies at "
        f"{card['test_precision']:.0%} precision. Both numbers matter: most flags are worth investigating, "
        f"and **most distressed companies are still missed**."
    )

# ================================================================ 3. DRILL-DOWN
elif view == "Company drill-down":
    page_header("Explainability", "Company drill-down")
    default = int(np.where(wl['rank'].values == wl['rank'].min())[0][0])
    name = st.selectbox("Select a company", wl.sort_values('rank')['company_name'].tolist(), index=default)
    row = wl[wl['company_name'] == name].iloc[0]
    lab, colr = band(row['risk_percentile'])

    a, b, c, d = st.columns(4)
    a.metric("Risk rank", f"#{int(row['rank'])}", f"of {len(wl):,}", delta_color="off")
    b.metric("Risk score", f"{row['risk_score']:.2f}", f"flag threshold {card['threshold']:.2f}", delta_color="off")
    c.metric("Percentile", f"{row['risk_percentile']:.1f}")
    d.metric("Model action", "FLAG" if row['flagged'] else "No flag")
    band_color = {"Elevated": "red", "Watch": "orange", "Moderate": "gray", "Low": "green"}[lab]
    status_color = {"Currently PN17/GN3": "red", "Previously classified": "orange",
                     "No classification on record": "gray"}.get(row['known_status'], "gray")
    st.markdown(
        f"<div class='dm-card' style='border-left:5px solid {colr};'>"
        f"<b>{name}</b> ({row['ticker'] if pd.notna(row['ticker']) else '—'}) · {row['sector']} · "
        f"period ending {row['period_end']}<br><br>"
        f"{tag(lab + ' risk', band_color)}{tag(row['known_status'], status_color)}</div>",
        unsafe_allow_html=True)
    st.write("")

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Why the model scored this company")
        srow = shap_df[shap_df['company_name'] == name]
        if len(srow):
            s = srow.iloc[0].drop('company_name').astype(float)
            s.index = [i[5:] for i in s.index]
            s = s[s.abs() > 1e-9].sort_values(key=abs, ascending=False).head(10).sort_values()
            if len(s):
                f = go.Figure(go.Bar(
                    x=s.values, y=[pretty(i) for i in s.index], orientation='h',
                    marker_color=['#FF3B30' if v > 0 else '#34C759' for v in s.values]))
                f.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0),
                                xaxis_title="Contribution to this company's risk score",
                                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(f, use_container_width=True)
                st.caption("Red pushes risk **up**, green pushes it **down** (SHAP contributions, this company only).")
            else:
                st.info("No individual feature moved this company's score materially away from the baseline.")
    with right:
        st.subheader("Risk score over time")
        h = rh[rh['company_name'] == name].sort_values('period_end')
        if len(h):
            f = go.Figure()
            f.add_trace(go.Scatter(x=h['period_end'], y=h['risk_score'], mode='lines+markers', name='Risk score',
                                   line=dict(color='#0071E3', width=2)))
            f.add_hline(y=card['threshold'], line_dash='dash', line_color='#FF3B30',
                        annotation_text='Flag threshold', annotation_position='top left')
            dd = h[h['pn17_gn3_label'] == 1]
            if len(dd):
                f.add_trace(go.Scatter(x=dd['period_end'], y=dd['risk_score'], mode='markers',
                                       name='Actually PN17/GN3', marker=dict(color='#FF3B30', size=12, symbol='x')))
            f.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0),
                            xaxis_title="", yaxis_title="Risk score",
                            legend=dict(orientation='h', y=1.12),
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(f, use_container_width=True)
            st.caption("Periods before 2025 were used in training; 2025 onward is held-out test data.")

    st.subheader("Financial indicators")
    ih = hist[hist['company_name'] == name].sort_values('period_end')
    base = [c for c in PRETTY if c in ih.columns]
    show = ih[['period_end'] + base].copy()
    show.columns = ['Period end'] + [PRETTY[c] for c in base]
    st.dataframe(show.style.format({c: '{:,.3f}' for c in show.columns if c != 'Period end'}, na_rep='—'),
                 hide_index=True, use_container_width=True)
    st.caption("Blank cells are genuinely missing in the source data, not zero. The model imputes these with the "
               "training-set median, which is itself a limitation (Chapter 5.4).")

# ================================================================ 4. TRENDS
elif view == "Indicator trends":
    page_header("Trend analysis", "Indicator trends",
        "Compare a financial indicator over time across companies.")
    c1, c2 = st.columns([2, 3])
    with c1:
        ind = st.selectbox("Indicator", list(PRETTY.keys()), format_func=lambda x: PRETTY[x])
    with c2:
        picks = st.multiselect(
            "Companies (default: current top 5 by risk)",
            wl.sort_values('rank')['company_name'].tolist(),
            default=wl.sort_values('rank')['company_name'].head(5).tolist())

    if picks:
        sub = hist[hist['company_name'].isin(picks)].sort_values('period_end')
        f = px.line(sub, x='period_end', y=ind, color='company_name', markers=True,
                    labels={'period_end': '', ind: PRETTY[ind], 'company_name': ''})
        dd = sub[sub['pn17_gn3_label'] == 1]
        if len(dd):
            f.add_trace(go.Scatter(x=dd['period_end'], y=dd[ind], mode='markers', name='PN17/GN3 period',
                                   marker=dict(color='#FF3B30', size=13, symbol='x')))
        f.update_layout(height=520, legend=dict(orientation='h', y=-0.18), margin=dict(l=0, r=0, t=10, b=0),
                         plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(f, use_container_width=True)
        st.caption("Red ✕ marks a period in which the company was officially PN17/GN3-classified. Gaps are missing data.")

        if ind == 'zscore_nonmanufacturing':
            st.info("The Altman Z''-Score distress threshold is 1.1. This project's own benchmark analysis "
                    "(Chapter 4.3) found it flags 13% of all Bursa company-periods — high recall, low precision.")

# ================================================================ 5. MODEL PERFORMANCE
elif view == "Model performance":
    page_header("Model evaluation", "Model performance",
        "Full evaluation of the calibrated one-step DQN on held-out 2025+ test data — the same numbers "
        "reported in Chapter 4 of the write-up, computed live by the same script that builds this dashboard.")

    m1, m2, m3 = st.columns(3)
    m1.metric("ROC-AUC", f"{metrics['roc_auc']:.3f}")
    m2.metric("PR-AUC", f"{metrics['pr_auc']:.3f}")
    m3.metric("F1", f"{metrics['f1_at_threshold']:.3f}")
    m4, m5, m6 = st.columns(3)
    m4.metric("Accuracy", f"{metrics['accuracy_at_threshold']:.1%}")
    m5.metric("Recall", f"{card['test_recall']:.1%}")
    m6.metric("Precision", f"{card['test_precision']:.1%}")

    st.warning(
        f"**Accuracy is misleading here — don't lean on it.** Only {card['test_positives']} of "
        f"{card['test_rows']:,} held-out rows are genuinely distressed (0.5%), so a model that flags "
        "nothing at all would already score 99.5% accuracy. ROC-AUC and PR-AUC are the numbers that "
        "actually measure ranking quality on this imbalanced problem — and **PR-AUC "
        f"({metrics['pr_auc']:.3f}) is the honest one**: it stays low precisely because true positives "
        "are so rare, which is the correct picture for this task, not a modelling failure to hide."
    )

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("ROC curve")
        f = go.Figure()
        f.add_trace(go.Scatter(x=metrics['roc_fpr'], y=metrics['roc_tpr'], mode='lines',
                                name=f"DQN (AUC={metrics['roc_auc']:.3f})", line=dict(color='#0071E3', width=2.5)))
        f.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines', name='Chance',
                                line=dict(color='#C7C7CC', dash='dash')))
        f.add_trace(go.Scatter(x=[metrics['altman_point']['fpr']], y=[metrics['altman_point']['tpr']],
                                mode='markers', name="Altman Z''-Score",
                                marker=dict(color='#FF9500', size=12, symbol='diamond')))
        f.add_trace(go.Scatter(x=[metrics['own_point']['fpr']], y=[metrics['own_point']['tpr']],
                                mode='markers', name='DQN @ calibrated threshold',
                                marker=dict(color='#FF3B30', size=12, symbol='star')))
        f.update_layout(height=420, xaxis_title="False positive rate", yaxis_title="True positive rate",
                         legend=dict(orientation='h', y=-0.2), margin=dict(l=0, r=0, t=10, b=0),
                         plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(f, use_container_width=True)
    with c2:
        st.subheader("Precision–recall curve")
        f = go.Figure()
        f.add_trace(go.Scatter(x=metrics['pr_recall'], y=metrics['pr_precision'], mode='lines',
                                name=f"DQN (AP={metrics['pr_auc']:.3f})", line=dict(color='#0071E3', width=2.5)))
        f.add_trace(go.Scatter(x=[metrics['altman_point']['recall']], y=[metrics['altman_point']['precision']],
                                mode='markers', name="Altman Z''-Score",
                                marker=dict(color='#FF9500', size=12, symbol='diamond')))
        f.update_layout(height=420, xaxis_title="Recall", yaxis_title="Precision",
                         legend=dict(orientation='h', y=-0.2), margin=dict(l=0, r=0, t=10, b=0),
                         plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(f, use_container_width=True)

    st.subheader("Confusion matrix — DQN at calibrated threshold")
    cm = metrics['confusion']
    c1, c2 = st.columns([1, 2])
    with c1:
        z = [[cm['TN'], cm['FP']], [cm['FN'], cm['TP']]]
        f = go.Figure(go.Heatmap(
            z=z, x=['Pred: Healthy', 'Pred: Distressed'], y=['Actual: Healthy', 'Actual: Distressed'],
            colorscale=[[0, '#F5F5F7'], [1, '#0071E3']], showscale=False,
            text=z, texttemplate="%{text:,}", textfont=dict(size=18)))
        f.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                         plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(f, use_container_width=True)
    with c2:
        st.markdown(f"""
<div class="dm-card">
<b>True positives:</b> {cm['TP']} — genuinely distressed companies correctly flagged<br>
<b>False positives:</b> {cm['FP']} — healthy companies incorrectly flagged<br>
<b>False negatives:</b> {cm['FN']} — genuinely distressed companies missed<br>
<b>True negatives:</b> {cm['TN']:,} — healthy companies correctly left unflagged
</div>
""", unsafe_allow_html=True)
        st.caption(
            "The class imbalance is visible directly in these counts: even a well-ranking model produces "
            "few true positives in absolute terms, because so few company-periods are genuinely distressed."
        )

    st.subheader("Cross-agent comparison")
    ac = pd.DataFrame(metrics['agent_comparison'])
    ac_disp = ac.rename(columns={'agent': 'Agent', 'TP': 'TP', 'FP': 'FP', 'FN': 'FN',
                                  'recall': 'Recall', 'precision': 'Precision', 'cost': 'Cost'})
    ac_disp['Recall'] = ac_disp['Recall'].map('{:.1%}'.format)
    ac_disp['Precision'] = ac_disp['Precision'].map('{:.1%}'.format)
    st.dataframe(ac_disp, hide_index=True, use_container_width=True)
    st.caption(
        "Cost = 10×(missed distress) + 3×(false alarm) on the same held-out test rows for every agent. "
        "Lower is better. Figures are read directly from each agent's own results file, never recomputed here."
    )

# ================================================================ 6. ABOUT & METHODOLOGY
else:
    page_header("Project overview", "About & methodology")

    st.markdown(f"""
<div class="dm-card">
<h4 style="margin-top:0;">{PROJECT_TITLE}</h4>
<p style="color:var(--ink-soft);margin-bottom:.3rem;">{PROJECT_CODE}</p>
<p style="margin-bottom:0;">Team: {' · '.join(TEAM)}</p>
</div>
""", unsafe_allow_html=True)

    st.markdown(
        "This dashboard is the artefact deliverable for **RQ4** of the capstone. It presents the output "
        "of reinforcement learning agents trained to flag Bursa Malaysia companies at risk of PN17/GN3 "
        "classification, benchmarked against the classical Altman Z''-Score model."
    )

    st.subheader("What this dashboard does")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("""**🔎 Monitor**
Every listed company is scored on its most recent reported financials and ranked by model risk score,
sector-by-sector or company-by-company.""")
    with f2:
        st.markdown("""**🧠 Explain**
Each flag is backed by a per-company SHAP breakdown showing exactly which indicators — and which
year-on-year changes — pushed the score up or down.""")
    with f3:
        st.markdown("""**📊 Evaluate**
The Model Performance page reports ROC-AUC, PR-AUC, F1, confusion matrix, and a like-for-like comparison
against every RL variant trained in this project and the Altman benchmark.""")

    st.subheader("Methodology, briefly")
    st.markdown(
        "- **Data**: quarterly/annual financial ratios for Bursa Malaysia listed companies, plus a historical "
        "record of PN17/GN3 classification dates (Chapter 3).\n"
        "- **State**: 16 features — 8 financial ratios (current ratio, quick ratio, cash ratio, ROA, ROE, "
        "net debt/total capital, asset turnover, Altman Z''-Score) plus their year-on-year deltas, robust "
        "median/IQR-scaled on the training split.\n"
        "- **Agents**: a one-step Deep Q-Network and a policy-gradient agent, each also trained as a "
        "multi-step MDP variant, using a reward function that front-loads credit for early, ahead-of-time "
        "detection of distress.\n"
        "- **Calibration**: decision thresholds are chosen on a held-out **validation** split to minimise "
        "misclassification cost, then evaluated once on a separate **test** split — never the reverse.\n"
        "- **Benchmark**: the classical Altman Z''-Score (threshold 1.1), computed directly from the same "
        "panel, with no RL involved — the yardstick the RL agents are measured against."
    )

    st.subheader("Performance on held-out test data")
    perf = pd.DataFrame([
        {"Method": "This model (calibrated DQN)", "Cost": card['test_cost'],
         "Recall": f"{card['test_recall']:.1%}", "Precision": f"{card['test_precision']:.1%}"},
        {"Method": "This model, at the Z-Score's recall", "Cost": card['recall_matched_cost'],
         "Recall": f"{card.get('recall_matched_recall', card['benchmark_altman_recall']):.1%}",
         "Precision": f"{card.get('recall_matched_precision', 0):.1%}"},
        {"Method": "Altman Z''-Score (classical benchmark)", "Cost": card['benchmark_altman_cost'],
         "Recall": f"{card['benchmark_altman_recall']:.1%}", "Precision": f"{card['benchmark_altman_precision']:.1%}"},
    ])
    st.dataframe(perf, hide_index=True, use_container_width=True)
    beats = card.get('recall_matched_beats_benchmark', True)
    st.caption(
        f"Cost = 10×(missed distress) + 3×(false alarm), on {card['test_rows']:,} held-out company-periods "
        f"containing {card['test_positives']} genuine distress cases. Lower is better. The model beats the classical "
        f"benchmark on cost at its own operating point" +
        (", and at the Z-Score's own detection rate too." if beats else
         f", but NOT at the Z-Score's own detection rate ({card['recall_matched_cost']} vs {card['benchmark_altman_cost']}) "
         "— pushed to match that recall, this model currently raises more false alarms than the classical rule does. "
         "This is disclosed rather than hidden: which operating point to trust is a real, current limitation, not settled.")
    )
    st.caption("See the **Model performance** page in the header nav for the full ROC/PR curves, confusion matrix, "
               "and cross-agent comparison.")

    st.subheader("What this model cannot do")
    st.error(
        f"**It misses most distressed companies.** At its default threshold it catches only {card['test_recall']:.0%} "
        "of them. It is a triage aid for deciding where to look first, not a substitute for credit analysis.\n\n"
        "**Its early-warning ability is unproven, not just largely unproven.** Every early flag measured in the "
        "current version of this project fell on data the model had trained on. One version briefly recorded a "
        "genuinely out-of-sample early warning — it did not reproduce after the next retrain, and is not repeated here.\n\n"
        "**It is trained on very few examples.** 46 distressed company-periods in training. Results have shifted "
        "materially across five versions of the data pipeline so far, mostly from data corrections rather than model "
        "changes — most recently, a single company's 3 training rows changed which of the two agents beats the "
        "benchmark at matched recall.\n\n"
        "**It is a backtest, not a live system.** Never validated on live forward data."
    )

    st.subheader("What drives the model overall")
    g = pd.DataFrame(gshap, columns=['feature', 'importance']).head(10).sort_values('importance')
    f = px.bar(g, x='importance', y=[pretty(x) for x in g['feature']], orientation='h',
               labels={'importance': 'Mean |SHAP| across test companies', 'y': ''})
    f.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0),
                     plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(f, use_container_width=True)
    st.caption("Year-on-year **changes** in liquidity outrank absolute levels — how fast a company is deteriorating "
               "carries more signal than where it currently stands.")

    st.subheader("Ideas for future value-added features")
    st.markdown(
        "- **Side-by-side company comparison** — pick two or more companies and overlay their indicator "
        "trajectories and SHAP breakdowns on one screen.\n"
        "- **Alert subscriptions** — email or webhook notification when a company newly crosses the flag threshold.\n"
        "- **Scenario/what-if slider** — let a user nudge one ratio (e.g. current ratio) and see the risk score "
        "recompute live, to build intuition for which indicators matter most.\n"
        "- **PDF one-pager export** — a printable company risk brief combining the drill-down panel and SHAP chart, "
        "for inclusion in a credit file.\n"
        "- **Live data refresh** — connect to a quarterly filings feed so the watchlist updates automatically "
        "instead of via manual pipeline reruns."
    )

    with st.expander("Full disclaimer"):
        st.markdown(
            "This dashboard is a research prototype produced for an academic capstone project and is **not** "
            "financial, investment, credit, or legal advice. It has not been validated on live, forward-looking "
            "data, is trained on a small number of historical distress examples, and both its recall and precision "
            "are limited (see Model Performance). Model outputs should be treated as a prompt for further human "
            "investigation, never as a standalone basis for any investment, lending, trading, or business decision. "
            "The authors and Sunway Business School accept no liability for decisions made using this tool."
        )

    with st.expander("Technical specification (model_card.json)"):
        st.json(card)

# ---------------------------------------------------------------- footer
st.markdown(f"""
<div class="dm-footer">
  <b>{PROJECT_TITLE}</b><br>
  {PROJECT_CODE}<br>
  Team: {' · '.join(TEAM)}<br><br>
  <b>Data sources:</b> Bursa Malaysia listed-company financials (LSEG/Refinitiv), PN17/GN3 historical
  classification records, Altman Z''-Score computed from the same panel.<br>
  <b>Disclaimer:</b> research prototype only — not financial, investment, or credit advice. See the
  About & methodology page for the full text.
</div>
""", unsafe_allow_html=True)
