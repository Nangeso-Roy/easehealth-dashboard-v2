"""
Ease Health Pilot Dashboard — main entry point.

Run with:
    streamlit run app.py
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.styles import inject as inject_css
from src.plot_theme import register as register_plot_theme, COLORS, PLOTLY_CONFIG
from src.data_loader import load_assessments, load_kobo
from src.render_geography import render_geography

from src.tabs import (
    feasibility, acceptability, clinical_confidence,
    adoption, clinical_activity, safety,
)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Ease Health Pilot",
    page_icon="◐",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"About": None, "Get help": None, "Report a bug": None},
)

inject_css()
register_plot_theme()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown("""
<div style="margin-bottom: 2rem;">
    <div style="font-size: 0.75rem; font-weight: 500; color: #94A3B8;
                text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.25rem;">
        Crane AI Labs · Google.org Pilot
    </div>
    <h1 style="margin: 0; font-size: 2rem; font-weight: 600; color: #0F172A;">
        Ease Health Pilot Dashboard
    </h1>
    <div style="margin-top: 0.5rem; color: #64748B; font-size: 0.9375rem;">
        Luweero District feasibility study · 27 April – 1 May 2026
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Load shared data once
# ---------------------------------------------------------------------------

assessments = load_assessments()
field_log = None  # field log form was never used; kept only for tab signature compatibility
kobo = load_kobo()


# ---------------------------------------------------------------------------
# Landing page (Snapshot)
# ---------------------------------------------------------------------------

def _render_landing():
    """The dashboard landing — six cards plus two charts."""

    total_assessments = len(assessments)
    distinct_devices = assessments["device_token"].nunique()
    distinct_conditions = assessments["condition_canonical"].dropna().nunique()
    facilities_visited = kobo["facility_clean"].dropna().nunique()

    inference_secs = assessments["inference_ms"].dropna() / 1000
    median_inference_s = inference_secs.median() if len(inference_secs) > 0 else None

    pilot_start = pd.Timestamp("2026-04-27").date()
    last_assessment_date = (
        assessments["client_date"].max() if len(assessments) > 0 else pilot_start
    )
    days_into_pilot = (last_assessment_date - pilot_start).days + 1

    # Six cards in two rows
    row1 = st.columns(3)
    with row1[0]:
        st.metric("Total assessments saved", f"{total_assessments}")
    with row1[1]:
        st.metric("Distinct devices", f"{distinct_devices}")
    with row1[2]:
        st.metric("Days into pilot", f"{days_into_pilot}")

    row2 = st.columns(3)
    with row2[0]:
        st.metric("Distinct conditions", f"{distinct_conditions}")
    with row2[1]:
        st.metric("Health facilities visited", f"{facilities_visited}")
    with row2[2]:
        if median_inference_s is not None:
            st.metric("Median inference time", f"{median_inference_s:.1f}s")
        else:
            st.metric("Median inference time", "—")

    st.markdown("<div style='margin-top: 2.5rem;'></div>", unsafe_allow_html=True)

    # Daily assessment volume chart
    st.markdown("### Daily assessment volume")

    daily = (
        assessments.groupby("client_date")
        .size()
        .reset_index(name="count")
        .sort_values("client_date")
    )
    all_dates = pd.date_range(pilot_start, last_assessment_date, freq="D").date
    daily = (
        pd.DataFrame({"client_date": all_dates})
        .merge(daily, on="client_date", how="left")
        .fillna({"count": 0})
    )

    fig_daily = go.Figure()
    fig_daily.add_trace(go.Bar(
        x=daily["client_date"],
        y=daily["count"],
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        hovertemplate="<b>%{x|%a %d %b}</b><br>%{y} assessments<extra></extra>",
    ))

    fig_daily.update_layout(
        height=320,
        showlegend=False,
        xaxis=dict(type="category"),
        yaxis=dict(title="Assessments", rangemode="tozero"),
        bargap=0.5,
        margin=dict(l=48, r=24, t=20, b=48),
    )
    fig_daily.update_xaxes(
        ticktext=[d.strftime("%a\n%d %b") for d in daily["client_date"]],
        tickvals=daily["client_date"],
    )

    st.plotly_chart(fig_daily, use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("<div style='margin-top: 2.5rem;'></div>", unsafe_allow_html=True)

    # Deployment reach choropleth (assessments per sub-county)
    render_geography(kobo)


# ---------------------------------------------------------------------------
# Tabbed layout
# ---------------------------------------------------------------------------

tab_snapshot, tab_feas, tab_accept, tab_conf, tab_adopt, tab_act, tab_safety = st.tabs([
    "Snapshot",
    "Feasibility",
    "Acceptability",
    "Clinical Confidence",
    "Adoption",
    "Clinical Activity",
    "Safety & AI Quality",
])

with tab_snapshot:
    _render_landing()

with tab_feas:
    feasibility.render(assessments, field_log, kobo)

with tab_accept:
    acceptability.render(assessments, field_log, kobo)

with tab_conf:
    clinical_confidence.render(assessments, field_log, kobo)

with tab_adopt:
    adoption.render(assessments, field_log, kobo)

with tab_act:
    clinical_activity.render(assessments, field_log, kobo)

with tab_safety:
    safety.render(assessments, field_log, kobo)


st.markdown("<div style='margin-top: 4rem;'></div>", unsafe_allow_html=True)