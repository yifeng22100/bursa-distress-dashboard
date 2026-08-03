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

st.set_page_config(page_title="Bursa Distress Monitor", page_icon="⚠️", layout="wide")

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
    return wl, sec, hist, rh, shap_df, card, gshap

wl, sec, hist, rh, shap_df, card, gshap = load()

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
    if pct >= 99.0: return "Elevated", "#B00020"
    if pct >= 95.0: return "Watch", "#E37400"
    if pct >= 80.0: return "Moderate", "#B8860B"
    return "Low", "#2E7D32"

# ---------------------------------------------------------------- sidebar
st.sidebar.title("⚠️ Distress Monitor")
st.sidebar.caption("Bursa Malaysia · PN17/GN3 early-warning prototype")
view = st.sidebar.radio(
    "View",
    ["Sector risk overview", "At-risk company ranking", "Company drill-down", "Indicator trends", "About this model"],
)
st.sidebar.markdown("---")
st.sidebar.metric("Companies monitored", f"{card['watchlist_companies']:,}")
st.sidebar.metric("Currently flagged", card['watchlist_flagged'])
st.sidebar.caption(
    f"Of the {card['watchlist_flagged']} companies flagged, {card['watchlist_flagged_true']} are genuinely "
    f"PN17/GN3-classified and {card['watchlist_flagged_false']} are not. **This model produces false alarms — "
    "flags are a prompt to look, not a conclusion.**"
)

# ================================================================ 1. SECTOR
if view == "Sector risk overview":
    st.title("Sector risk overview")
    st.caption(
        "Model risk score aggregated by sector, across each company's most recent reported period. "
        "Use this to decide where to look first — not as a verdict on any sector."
    )

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
            color=metric, color_continuous_scale=['#2E7D32', '#B8860B', '#E37400', '#B00020'],
            labels={metric: lbl, 'sector': ''},
            hover_data={'companies': True, 'flagged': True, 'currently_distressed': True, metric: ':.2f'},
        )
        fig.update_layout(height=520, coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0))
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
    st.title("At-risk company ranking")
    st.caption("Every monitored company, ranked by model risk score on its most recent reported period.")

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        secs = st.multiselect("Filter by sector", sorted(wl['sector'].unique()))
    with c2:
        stat = st.multiselect("Filter by known status", sorted(wl['known_status'].unique()))
    with c3:
        only_flagged = st.checkbox("Flagged only", value=False)

    v = wl.copy()
    if secs: v = v[v['sector'].isin(secs)]
    if stat: v = v[v['known_status'].isin(stat)]
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
    st.title("Company drill-down")
    default = int(np.where(wl['rank'].values == wl['rank'].min())[0][0])
    name = st.selectbox("Select a company", wl.sort_values('rank')['company_name'].tolist(), index=default)
    row = wl[wl['company_name'] == name].iloc[0]
    lab, colr = band(row['risk_percentile'])

    a, b, c, d = st.columns(4)
    a.metric("Risk rank", f"#{int(row['rank'])}", f"of {len(wl):,}", delta_color="off")
    b.metric("Risk score", f"{row['risk_score']:.2f}", f"flag threshold {card['threshold']:.2f}", delta_color="off")
    c.metric("Percentile", f"{row['risk_percentile']:.1f}")
    d.metric("Model action", "FLAG" if row['flagged'] else "No flag")
    st.markdown(
        f"<div style='padding:.6rem 1rem;border-left:5px solid {colr};background:#00000008;'>"
        f"<b>{name}</b> ({row['ticker'] if pd.notna(row['ticker']) else '—'}) · {row['sector']} · "
        f"period ending {row['period_end']}<br><b style='color:{colr}'>{lab} risk</b> · "
        f"Known status: {row['known_status']}</div>", unsafe_allow_html=True)
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
                    marker_color=['#B00020' if v > 0 else '#2E7D32' for v in s.values]))
                f.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0),
                                xaxis_title="Contribution to this company's risk score")
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
                                   line=dict(color='#1f3b73', width=2)))
            f.add_hline(y=card['threshold'], line_dash='dash', line_color='#B00020',
                        annotation_text='Flag threshold', annotation_position='top left')
            dd = h[h['pn17_gn3_label'] == 1]
            if len(dd):
                f.add_trace(go.Scatter(x=dd['period_end'], y=dd['risk_score'], mode='markers',
                                       name='Actually PN17/GN3', marker=dict(color='#B00020', size=12, symbol='x')))
            f.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0),
                            xaxis_title="", yaxis_title="Risk score",
                            legend=dict(orientation='h', y=1.12))
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
    st.title("Indicator trends")
    st.caption("Compare a financial indicator over time across companies.")
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
                                   marker=dict(color='#B00020', size=13, symbol='x')))
        f.update_layout(height=520, legend=dict(orientation='h', y=-0.18), margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(f, use_container_width=True)
        st.caption("Red ✕ marks a period in which the company was officially PN17/GN3-classified. Gaps are missing data.")

        if ind == 'zscore_nonmanufacturing':
            st.info("The Altman Z''-Score distress threshold is 1.1. This project's own benchmark analysis "
                    "(Chapter 4.3) found it flags 13% of all Bursa company-periods — high recall, low precision.")

# ================================================================ 5. ABOUT
else:
    st.title("About this model")
    st.markdown(
        "This dashboard is the artefact deliverable for **RQ4** of a Master of Business Analytics capstone "
        "(PRJ5158, Sunway Business School). It presents the output of a reinforcement learning agent trained to "
        "flag Bursa Malaysia companies at risk of PN17/GN3 classification, benchmarked against the Altman Z''-Score."
    )
    st.subheader("Performance on held-out test data")
    perf = pd.DataFrame([
        {"Method": "This model (calibrated DQN)", "Cost": card['test_cost'],
         "Recall": f"{card['test_recall']:.1%}", "Precision": f"{card['test_precision']:.1%}"},
        {"Method": "This model, at the Z-Score's recall", "Cost": card['recall_matched_cost'],
         "Recall": f"{card['benchmark_altman_recall']:.1%}", "Precision": "9.8%"},
        {"Method": "Altman Z''-Score (classical benchmark)", "Cost": card['benchmark_altman_cost'],
         "Recall": f"{card['benchmark_altman_recall']:.1%}", "Precision": f"{card['benchmark_altman_precision']:.1%}"},
    ])
    st.dataframe(perf, hide_index=True, use_container_width=True)
    st.caption(
        "Cost = 10×(missed distress) + 3×(false alarm), on 1,740 held-out company-periods containing 19 genuine "
        "distress cases. Lower is better. The model beats the classical benchmark on cost at both operating points, "
        "mainly by raising far fewer false alarms at the same detection rate."
    )

    st.subheader("What this model cannot do")
    st.error(
        "**It misses most distressed companies.** At its default threshold it catches roughly a quarter of them. "
        "It is a triage aid for deciding where to look first, not a substitute for credit analysis.\n\n"
        "**Its early-warning ability is largely unproven.** Nearly every early flag measured in this project fell on "
        "data the model had trained on. Exactly one genuine out-of-sample early warning was recorded.\n\n"
        "**It is trained on very few examples.** 46 distressed company-periods in training. Results shifted "
        "materially across four versions of the data pipeline, mostly from data corrections rather than model changes.\n\n"
        "**It is a backtest, not a live system.** Never validated on live forward data."
    )

    st.subheader("What drives the model overall")
    g = pd.DataFrame(gshap, columns=['feature', 'importance']).head(10).sort_values('importance')
    f = px.bar(g, x='importance', y=[pretty(x) for x in g['feature']], orientation='h',
               labels={'importance': 'Mean |SHAP| across test companies', 'y': ''})
    f.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(f, use_container_width=True)
    st.caption("Year-on-year **changes** in liquidity outrank absolute levels — how fast a company is deteriorating "
               "carries more signal than where it currently stands.")

    with st.expander("Technical specification"):
        st.json(card)
