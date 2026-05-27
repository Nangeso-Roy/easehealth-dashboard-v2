"""Adoption tab — Q14, Q15 (per finalized analysis map).

Q14: the recognised drivers of technology adoption (radar).
Q15: how those drivers move together (correlation heatmap, descriptive only).
Q16-Q19 are not built (dead: depend on a valid measure of actual usage).
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.plot_theme import COLORS, PLOTLY_CONFIG, SEQ_SCALE

# subscale column -> plain-language driver name
DRIVERS = [
    ("pu_mean", "Usefulness"),
    ("peou_mean", "Ease of use"),
    ("si_mean", "Encouragement from peers & managers"),
    ("fc_mean", "Right support & conditions"),
    ("ai_mean", "Intend to keep using"),
]


def render(assessments, field_log, kobo):
    st.markdown("### Adoption")
    st.markdown(
        "<div style='color: #64748B; margin-bottom: 1.5rem;'>"
        "The recognised drivers of whether people take up a new tool: how the app scored "
        "on each, and how the drivers relate to one another."
        "</div>",
        unsafe_allow_html=True,
    )

    if len(kobo) == 0:
        st.info("No health-worker responses yet.")
        return

    present = [(c, lbl) for c, lbl in DRIVERS if c in kobo.columns]
    if not present:
        st.info("Adoption data not available.")
        return

    means = {lbl: kobo[c].mean() for c, lbl in present}

    # ---------------------------------------------------------------------
    # Q14 — radar of the five drivers
    # ---------------------------------------------------------------------

    st.markdown("#### How the app scored on each driver")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "Average rating out of 5 on each driver of adoption, ranked from highest to "
        "lowest. The scores sit close together, so the scale below starts above zero to "
        "make the differences visible."
        "</div>",
        unsafe_allow_html=True,
    )

    ranked = sorted(means.items(), key=lambda kv: kv[1])  # ascending so highest plots at top
    labels = [k for k, _ in ranked]
    values = [v for _, v in ranked]

    lo = min(values)
    x_start = max(1.0, lo - 0.5)  # start the line a little below the lowest score

    fig_lolly = go.Figure()
    # stems
    for lbl, val in zip(labels, values):
        fig_lolly.add_trace(go.Scatter(
            x=[x_start, val], y=[lbl, lbl],
            mode="lines",
            line=dict(color=COLORS["hair"], width=2),
            hoverinfo="skip", showlegend=False,
        ))
    # dots + value labels
    fig_lolly.add_trace(go.Scatter(
        x=values, y=labels,
        mode="markers+text",
        marker=dict(size=14, color=COLORS["primary"], line=dict(width=2, color="#FFFFFF")),
        text=[f"{v:.1f}" for v in values],
        textposition="middle right", textfont=dict(size=12, color=COLORS["text_secondary"]),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{x:.1f} out of 5<extra></extra>",
        showlegend=False,
    ))
    fig_lolly.update_layout(
        height=320,
        xaxis=dict(title="Average rating (out of 5)", range=[x_start, 5],
                   showgrid=True, gridcolor="#F1F5F9", zeroline=False),
        yaxis=dict(title="", automargin=True, tickfont=dict(size=13, color="#475569")),
        margin=dict(l=24, r=80, t=20, b=48),
    )
    st.plotly_chart(fig_lolly, use_container_width=True, config=PLOTLY_CONFIG)
    st.markdown(
        "<div style='color: #64748B; font-size: 0.8125rem; margin-top: -0.5rem;'>"
        "<i>All five drivers scored close to 4 out of 5, broadly favourable across the board.</i></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q15 — correlation heatmap (descriptive)
    # ---------------------------------------------------------------------

    st.markdown("#### Which drivers move together")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "When health workers rated one driver highly, did they tend to rate another highly "
        "too? Darker means a stronger link. This is exploratory: it shows association, not cause."
        "</div>",
        unsafe_allow_html=True,
    )

    cols = [c for c, _ in present]
    short_labels = [lbl for _, lbl in present]
    corr = kobo[cols].corr()

    # Per-cell text colour: white on dark cells, dark on light cells, so the
    # numbers stay legible across the whole ramp.
    annotations = []
    n = len(short_labels)
    for i in range(n):
        for j in range(n):
            val = corr.values[i][j]
            txt_color = "#FFFFFF" if val >= 0.55 else "#0F172A"
            annotations.append(dict(
                x=short_labels[j], y=short_labels[i],
                text=f"{val:.2f}", showarrow=False,
                font=dict(size=12, color=txt_color, family="Inter"),
            ))

    fig_corr = go.Figure(go.Heatmap(
        z=corr.values,
        x=short_labels,
        y=short_labels,
        zmin=0, zmax=1,
        colorscale=SEQ_SCALE,
        hovertemplate="<b>%{y}</b> & <b>%{x}</b><br>link: %{z:.2f}<extra></extra>",
        colorbar=dict(thickness=12, len=0.7, tickfont=dict(size=11, color="#64748B"), outlinewidth=0),
    ))
    fig_corr.update_layout(
        height=460,
        annotations=annotations,
        xaxis=dict(tickangle=-25, tickfont=dict(size=11, color=COLORS["text_secondary"])),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11, color=COLORS["text_secondary"])),
        margin=dict(l=24, r=24, t=20, b=120),
    )
    st.plotly_chart(fig_corr, use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("<div style='margin-top: 2.5rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='border-left: 3px solid #E2E8F0; padding: 0.5rem 1rem;
                    color: #64748B; font-size: 0.875rem; line-height: 1.6;'>
        <strong style='color: #475569;'>About this tab</strong><br>
        The five drivers come from a standard, widely-used framework for understanding why
        people adopt new technology. All ratings come from interviews with the health workers
        who used the app. The links between drivers are exploratory and describe association,
        not cause.
        </div>
        """,
        unsafe_allow_html=True,
    )
