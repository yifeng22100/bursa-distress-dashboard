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
                    initial_sidebar_state="expanded")

# ---------------------------------------------------------------- design system
# Font: National (HBR's sans-serif) is a paid Commercial Type / Klim Type Foundry font, not
# distributable as a web font without a licence this project doesn't hold -- same constraint as
# Google Sans. It's listed first in case a viewer happens to have it installed locally, then
# falls back to Inter, a free grotesque with very similar proportions and neutrality, loaded from
# Google Fonts -- that's what almost every viewer will actually see.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
:root{
  --bg:#FFFFFF; --card:#FFFFFF; --ink:#1D1D1F; --ink-soft:#6E6E73;
  --line:#E5E5EA; --blue:#0071E3; --red:#FF3B30; --orange:#FF9500;
  --green:#34C759; --gold:#B8860B;
  --primary-color:#0071E3;
}
html, body, [class*="css"]{
  font-family:"National","National 2",Inter,-apple-system,BlinkMacSystemFont,
              "Helvetica Neue",Arial,sans-serif !important;
  color:var(--ink);
}
.stApp{ background:var(--bg); }
/* Streamlit Community Cloud renders this app inside a cross-origin iframe and draws its own
   "Fork / GitHub / menu" toolbar OVER that iframe from the parent page -- our CSS/JS has zero
   access to that parent frame, cannot measure its real height, and cannot hide it. padding-top:0
   here previously pushed our masthead flush to the top of the iframe, i.e. directly under that
   toolbar, which is what was covering the brand title. This fixed clearance is a guess with
   margin for safety, not a measurement -- there is no way to do better from inside the iframe. */
.block-container{ max-width:1200px; padding-top:4.5rem !important; }

/* ---- sidebar: brand + vertical nav + quick stats, replacing the old top nav bar. The top
   masthead/stat-band strip is gone — this is now the single place branding and navigation live,
   closer to how Bloomberg/PitchBook-style analyst tools are actually laid out. ---- */
section[data-testid="stSidebar"]{
  background:#FAFAFB; border-right:1px solid var(--line);
}
/* Same Cloud-toolbar-overlay clearance issue as the main content area (see block-container
   above) applies to the sidebar's top edge too, since the overlay spans the full viewport width. */
section[data-testid="stSidebar"] div[data-testid="stSidebarContent"],
section[data-testid="stSidebar"] > div:first-child{ padding-top:2rem; }
.dm-sb-brand{ font-size:1.15rem; font-weight:900; letter-spacing:-0.01em; color:var(--ink); margin-bottom:.15rem; }
.dm-sb-brand span{ color:var(--blue); }
.dm-sb-tagline{ font-size:.74rem; color:var(--ink-soft); line-height:1.4; margin-bottom:1.1rem; }
.dm-sb-stats{ display:flex; gap:1rem; margin:.9rem 0 .6rem 0; }
.dm-sb-stat b{ font-size:1.3rem; font-weight:700; color:var(--ink); display:block; line-height:1.1; }
.dm-sb-stat span{ font-size:.68rem; color:var(--ink-soft); }
.dm-sb-note{ font-size:.7rem; color:var(--ink-soft); line-height:1.4; margin-top:.4rem; }

/* Sidebar nav: a clean vertical list, not a radio group — no dot, full-width rows, a left
   accent bar and tinted background on the active item. */
section[data-testid="stSidebar"] div[role="radiogroup"]{ gap:.1rem; flex-direction:column; }
section[data-testid="stSidebar"] div[role="radiogroup"] label{
  background:none; border-radius:8px; padding:.5rem .6rem; margin:0; width:100%;
  border-left:3px solid transparent; color:var(--ink-soft); font-weight:500; font-size:.92rem;
  transition:background .15s ease, color .15s ease;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{ background:#EFEFF2; color:var(--ink); }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){
  background:#EAF2FE; color:var(--blue); font-weight:700; border-left-color:var(--blue);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child{ display:none; }

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
/* stMetricValue's default font-size is large enough that 3+ metric columns in the main content
   area (now narrower, since the sidebar takes ~300px) clip to an ellipsis -- e.g. "99.0%" showing
   as "99...". Capping the font-size and letting it wrap instead of truncate fixes this everywhere
   metrics are used, rather than patching each page's column count individually. */
[data-testid="stMetric"]{
  background:var(--card); border:1px solid var(--line); border-radius:14px;
  padding:.7rem .9rem; box-shadow:0 1px 3px rgba(0,0,0,.04);
}
[data-testid="stMetricLabel"]{ color:var(--ink-soft); }
[data-testid="stMetricValue"]{
  font-size:1.65rem !important; white-space:normal !important; overflow:visible !important;
  text-overflow:clip !important;
}

/* ---- dataframe / table corners ---- */
[data-testid="stDataFrame"]{ border-radius:14px; overflow:hidden; border:1px solid var(--line); }

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
    weights = json.load(open(f"{DATA}/model_weights.json"))
    try:
        changes = json.load(open(f"{DATA}/watchlist_changes.json"))
    except FileNotFoundError:
        changes = dict(newly_flagged=[], newly_cleared=[], had_previous_run=False)
    return wl, sec, hist, rh, shap_df, card, gshap, metrics, weights, changes

wl, sec, hist, rh, shap_df, card, gshap, metrics, weights, changes = load()

def mlp_forward(x):
    """Pure-numpy replay of the frozen DQN's forward pass (weights exported to JSON so the
    deployed app doesn't need a torch install just to run 3 matrix multiplies). Returns the
    'flag' Q-value, the same quantity risk_score is throughout the rest of the app."""
    h1 = np.maximum(0, x @ np.array(weights['w0']).T + np.array(weights['b0']))
    h2 = np.maximum(0, h1 @ np.array(weights['w2']).T + np.array(weights['b2']))
    out = h2 @ np.array(weights['w4']).T + np.array(weights['b4'])
    return out[..., 2]

def score_scenario(raw_values):
    """raw_values: dict of the 8 base ratios (unscaled) plus their 8 year-on-year deltas,
    in weights['feature_cols'] order. Applies the same robust median/IQR scaling used in
    training before scoring."""
    x = np.array([raw_values[c] for c in weights['feature_cols']], dtype=float)
    med = np.array([weights['medians'][c] for c in weights['feature_cols']])
    iqr = np.array([weights['iqr'][c] for c in weights['feature_cols']])
    x = np.clip((x - med) / iqr, -weights['clip'], weights['clip'])
    return float(mlp_forward(x))

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

# ---------------------------------------------------------------- sidebar: brand + nav + stats
NAV = ["Welcome", "Sector risk overview", "At-risk company ranking", "Company drill-down",
       "Company comparison", "Indicator trends", "Model performance", "About & methodology"]
# A widget's session_state key can't be reassigned after that widget has run this script pass,
# so a landing-page button can't set st.session_state["nav"] directly -- it stashes the request
# in a separate key instead, applied here, BEFORE the radio widget below is instantiated.
if "nav_request" in st.session_state:
    st.session_state["nav"] = st.session_state.pop("nav_request")
if "nav" not in st.session_state:
    st.session_state["nav"] = "Welcome"

with st.sidebar:
    st.markdown(f"""
<div class="dm-sb-brand">⚠️ Bursa <span>Distress</span> Monitor</div>
<div class="dm-sb-tagline">RL early-warning prototype for PN17/GN3 classification · Chapter 4.8
artefact (RQ4)<br>{PROJECT_CODE}</div>
""", unsafe_allow_html=True)
    view = st.radio("Navigate", NAV, label_visibility="collapsed", key="nav")
    st.markdown(f"""
<div class="dm-sb-stats">
  <div class="dm-sb-stat"><b>{len(wl):,}</b><span>companies monitored</span></div>
  <div class="dm-sb-stat"><b>{card['watchlist_flagged']}</b><span>currently flagged</span></div>
</div>
{tag(f"{card['watchlist_flagged_true']} genuine", "green")}{tag(f"{card['watchlist_flagged_false']} false alarms", "orange")}
<div class="dm-sb-note">Flags are a prompt to look, not a conclusion.</div>
""", unsafe_allow_html=True)

def goto(tab_name, key):
    if st.button(f"Open {tab_name} →", key=key):
        st.session_state["nav_request"] = tab_name
        st.rerun()

st.markdown(f"""
<div class="dm-banner dm-banner-disclaimer">
  ⚠️ <b>Disclaimer.</b> This is a student research prototype, not financial or investment advice.
  It flags companies for further human review and misses most distressed companies at its default
  threshold (recall {card['test_recall']:.0%} on held-out test data). Do not use it, alone or in
  combination with other information, to make investment, lending, or credit decisions.
</div>
""", unsafe_allow_html=True)

if changes['had_previous_run'] and (changes['newly_flagged'] or changes['newly_cleared']):
    bits = []
    if changes['newly_flagged']:
        bits.append(f"<b>{len(changes['newly_flagged'])} newly flagged</b>: " + ", ".join(changes['newly_flagged']))
    if changes['newly_cleared']:
        bits.append(f"<b>{len(changes['newly_cleared'])} cleared</b>: " + ", ".join(changes['newly_cleared']))
    st.markdown(f"""
<div class="dm-banner" style="background:#EAF2FE;border-color:#C7DFFB;color:#0058C6;">
  🔔 <b>Since the last rebuild:</b> {" · ".join(bits)}.
</div>
""", unsafe_allow_html=True)

# ================================================================ 0. WELCOME
if view == "Welcome":
    page_header("Welcome", "Know which Bursa Malaysia companies deserve a second look.",
        "A reinforcement-learning early-warning system for corporate financial distress (PN17/GN3 "
        "classification), benchmarked against the classical Altman Z''-Score — built as a research "
        "artefact, not a trading or lending tool.")

    st.subheader("Who this is for")
    st.markdown("""
<div class="dm-card">📈 <b>Investors & analysts.</b> A triage aid for deciding which of 1,065
companies to look at first — not a buy/sell signal, and not a substitute for reading the actual
financials.</div>
<div class="dm-card">🏦 <b>Credit & risk teams.</b> A second opinion alongside the Altman
Z''-Score, with every flag traceable to the specific indicators that drove it (SHAP), so it can
be argued for or against in a credit file.</div>
<div class="dm-card">🎓 <b>Students & RL enthusiasts.</b> A worked, honestly-reported example of
applying reinforcement learning to a real, small, severely imbalanced dataset — including what
didn't work and why.</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="dm-banner" style="background:#FFF7ED;border-color:#FFE0B2;color:#7A4A00;">
⚠️ Read this before anything else: this model catches only about 1 in 5 genuinely distressed
companies at its default setting, and every flag needs human judgement. See the disclaimer below
and the full text on the About & methodology page.
</div>""", unsafe_allow_html=True)

    st.subheader("How to use this dashboard")
    st.caption("Seven views, each answering a different question. Click through, or use the tabs above.")

    guide = [
        ("Sector risk overview", "🏭", "Where should I start looking?",
         "Aggregates risk to the sector level so you can decide which industries warrant attention first."),
        ("At-risk company ranking", "📋", "Show me the working watchlist.",
         "Every monitored company ranked by risk score, filterable by sector and status, with a CSV export."),
        ("Company drill-down", "🔍", "Why is this one company flagged?",
         "Rank, score, a SHAP explanation of what drove it, risk history, and a live what-if slider."),
        ("Company comparison", "⚖️", "How does A stack up against B and C?",
         "Put 2–4 companies side by side — trajectory, current standing, and what's driving each score."),
        ("Indicator trends", "📉", "How has one ratio moved over time?",
         "Compare any single financial indicator across companies, with actual distress periods marked."),
        ("Model performance", "📊", "Can I trust this model? Show me the numbers.",
         "ROC/PR curves, confusion matrix, and a like-for-like comparison against every agent trained."),
        ("About & methodology", "📖", "What is this, exactly, and how was it built?",
         "Project background, methodology, limitations, and the full disclaimer."),
    ]
    for i in range(0, len(guide), 2):
        cols = st.columns(2)
        for col, (name, icon, question, desc) in zip(cols, guide[i:i + 2]):
            with col:
                st.markdown(f"""
<div class="dm-card">
<span style="font-size:1.3rem;">{icon}</span> <b>{name}</b><br>
<span style="color:var(--ink-soft);font-style:italic;">"{question}"</span><br><br>
{desc}
</div>""", unsafe_allow_html=True)
                goto(name, f"goto_{name}")

# ================================================================ 1. SECTOR
elif view == "Sector risk overview":
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

    # Stacked, not side-by-side: this horizontal bar chart's long sector-name labels blow past
    # Plotly's auto-margin at the narrower widths this main content area now has (since the
    # sidebar takes ~300px) and overlapped whatever sat in the column beside it.
    top = view_sec.nlargest(15, metric).sort_values(metric)
    lbl = {'median_risk': 'Median risk score', 'mean_risk': 'Mean risk score',
           'flagged_pct': '% of companies flagged'}[metric]
    fig = px.bar(
        top, x=metric, y='sector', orientation='h',
        color=metric, color_continuous_scale=['#34C759', '#B8860B', '#FF9500', '#FF3B30'],
        labels={metric: lbl, 'sector': ''},
        hover_data={'companies': True, 'flagged': True, 'currently_distressed': True, metric: ':.2f'},
    )
    fig.update_layout(height=520, coloraxis_showscale=False, margin=dict(l=10, r=10, t=10, b=10),
                       plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

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

    c1, c2 = st.columns(2)
    with c1:
        secs = st.multiselect("Filter by sector", sorted(wl['sector'].unique()))
    with c2:
        stat = st.multiselect("Filter by known status", sorted(wl['known_status'].unique()))
    c3, c4 = st.columns([3, 1])
    with c3:
        search = st.text_input("Search company name", placeholder="e.g. Sentoria")
    with c4:
        st.write("")
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

    a, b = st.columns(2)
    a.metric("Risk rank", f"#{int(row['rank'])}", f"of {len(wl):,}", delta_color="off")
    b.metric("Risk score", f"{row['risk_score']:.2f}", f"flag threshold {card['threshold']:.2f}", delta_color="off")
    c, d = st.columns(2)
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

    ih_sorted = ih.reset_index(drop=True)
    if len(ih_sorted):
        with st.expander("What-if: explore this company's risk score"):
            st.caption(
                "Nudge this company's most recent indicators and see how the model's risk score reacts. "
                "Runs the same frozen network used everywhere else in this dashboard, entirely in your "
                "browser session — nothing is retrained, and nothing you enter here is saved."
            )
            latest_row = ih_sorted.iloc[-1]
            prev_row = ih_sorted.iloc[-2] if len(ih_sorted) >= 2 else None
            new_vals = {}
            cols = st.columns(4)
            for i, f in enumerate(base):
                default = latest_row[f]
                default = float(default) if pd.notna(default) else float(weights['medians'][f])
                colvals = hist[f].dropna()
                lo, hi = float(colvals.quantile(0.02)), float(colvals.quantile(0.98))
                if lo >= hi:
                    lo, hi = default - 1, default + 1
                with cols[i % 4]:
                    new_vals[f] = st.slider(PRETTY[f], min_value=lo, max_value=hi,
                                             value=min(max(default, lo), hi), key=f"whatif_{f}")

            scenario = {}
            for f in base:
                scenario[f] = new_vals[f]
                prev_val = prev_row[f] if prev_row is not None else np.nan
                scenario[f + '_delta'] = (new_vals[f] - prev_val) if pd.notna(prev_val) else np.nan
            for c in weights['feature_cols']:
                if c not in scenario or pd.isna(scenario.get(c, np.nan)):
                    scenario[c] = weights['medians'][c]

            new_score = score_scenario(scenario)
            orig_score = float(row['risk_score'])
            wc1, wc2, wc3 = st.columns(3)
            wc1.metric("Original risk score", f"{orig_score:.2f}")
            wc2.metric("What-if risk score", f"{new_score:.2f}", f"{new_score - orig_score:+.2f}")
            new_flag = new_score > card['threshold']
            wc3.metric("What-if model action", "FLAG" if new_flag else "No flag")
            if new_flag != bool(row['flagged']):
                st.warning("This scenario **flips the flag decision** relative to the company's actual latest data.")

# ================================================================ COMPARISON
elif view == "Company comparison":
    page_header("Side-by-side view", "Company comparison",
        "Put two to four companies next to each other — risk trajectory, current standing, and "
        "what's driving each score.")

    default_picks = wl.sort_values('rank')['company_name'].head(3).tolist()
    picks = st.multiselect("Companies to compare (2–4)", wl.sort_values('rank')['company_name'].tolist(),
                            default=default_picks, max_selections=4)

    if len(picks) < 2:
        st.info("Pick at least two companies to compare.")
    else:
        colors = ['#0071E3', '#FF3B30', '#34C759', '#FF9500']
        cmp_cols = st.columns(len(picks))
        for i, name in enumerate(picks):
            r = wl[wl['company_name'] == name].iloc[0]
            lab, colr = band(r['risk_percentile'])
            band_color = {"Elevated": "red", "Watch": "orange", "Moderate": "gray", "Low": "green"}[lab]
            with cmp_cols[i]:
                st.markdown(f"""
<div class="dm-card" style="border-top:4px solid {colors[i]};">
<b>{name}</b><br><span style="color:var(--ink-soft);font-size:.82rem;">{r['sector']}</span><br><br>
Rank <b>#{int(r['rank'])}</b> of {len(wl):,}<br>
Score <b>{r['risk_score']:.2f}</b><br><br>
{tag(lab + ' risk', band_color)}
</div>""", unsafe_allow_html=True)

        st.subheader("Risk score over time")
        f = go.Figure()
        for i, name in enumerate(picks):
            h = rh[rh['company_name'] == name].sort_values('period_end')
            f.add_trace(go.Scatter(x=h['period_end'], y=h['risk_score'], mode='lines+markers',
                                    name=name, line=dict(color=colors[i], width=2)))
        f.add_hline(y=card['threshold'], line_dash='dash', line_color='#6E6E73',
                    annotation_text='Flag threshold', annotation_position='top left')
        f.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Risk score",
                         legend=dict(orientation='h', y=1.12),
                         plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(f, use_container_width=True)

        st.subheader("Indicator comparison")
        ind = st.selectbox("Indicator", list(PRETTY.keys()), format_func=lambda x: PRETTY[x], key="cmp_ind")
        f2 = px.line(hist[hist['company_name'].isin(picks)].sort_values('period_end'),
                     x='period_end', y=ind, color='company_name', markers=True,
                     color_discrete_sequence=colors, labels={'period_end': '', ind: PRETTY[ind], 'company_name': ''})
        f2.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation='h', y=-0.2),
                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(f2, use_container_width=True)

        st.subheader("What's driving each score")
        shap_cols = st.columns(len(picks))
        for i, name in enumerate(picks):
            srow = shap_df[shap_df['company_name'] == name]
            with shap_cols[i]:
                st.markdown(f"**{name}**")
                if len(srow):
                    s = srow.iloc[0].drop('company_name').astype(float)
                    s.index = [j[5:] for j in s.index]
                    s = s[s.abs() > 1e-9].sort_values(key=abs, ascending=False).head(5).sort_values()
                    if len(s):
                        f3 = go.Figure(go.Bar(
                            x=s.values, y=[pretty(j) for j in s.index], orientation='h',
                            marker_color=['#FF3B30' if v > 0 else '#34C759' for v in s.values]))
                        f3.update_layout(height=220, margin=dict(l=0, r=0, t=10, b=0),
                                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(f3, use_container_width=True)
                    else:
                        st.caption("No feature moved this score materially.")

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
    st.markdown("""
<div class="dm-card">🔎 <b>Monitor.</b> Every listed company is scored on its most recent reported
financials and ranked by model risk score, sector-by-sector or company-by-company.</div>
<div class="dm-card">🧠 <b>Explain.</b> Each flag is backed by a per-company SHAP breakdown showing
exactly which indicators — and which year-on-year changes — pushed the score up or down.</div>
<div class="dm-card">📊 <b>Evaluate.</b> The Model Performance page reports ROC-AUC, PR-AUC, F1,
confusion matrix, and a like-for-like comparison against every RL variant trained in this project
and the Altman benchmark.</div>
""", unsafe_allow_html=True)

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
