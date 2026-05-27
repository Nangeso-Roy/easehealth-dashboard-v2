"""Clinical Confidence tab — Q12, Q13 (per finalized analysis map).

Q12: confidence before vs after the app, across eight clinical areas (slopegraph).
Q13: change per area (before -> now).
Both are self-reported and recalled at the end interview (not a measured baseline).
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.plot_theme import COLORS, PLOTLY_CONFIG

# (pre_col, post_col, friendly label) for the eight clinical areas
F_DOMAINS = [
    ("f01_mal_pre", "f01_mal_post", "Assessing malaria symptoms"),
    ("f02_mal_tx_pre", "f02_mal_tx_post", "Deciding on malaria treatment"),
    ("f03_pneu_pre", "f03_pneu_post", "Assessing pneumonia symptoms"),
    ("f04_pneu_tx_pre", "f04_pneu_tx_post", "Deciding on pneumonia treatment"),
    ("f05_tb_pre", "f05_tb_post", "Identifying suspected TB"),
    ("f06_edu_pre", "f06_edu_post", "Providing health education"),
    ("f07_ref_pre", "f07_ref_post", "Knowing when to refer a patient"),
    ("f08_uncert_pre", "f08_uncert_post", "Deciding when unsure"),
]


def render(assessments, field_log, kobo):
    st.markdown("### Clinical Confidence")
    st.markdown(
        "<div style='color: #64748B; margin-bottom: 1.5rem;'>"
        "How confident health workers felt managing common conditions before they used "
        "the app, compared with after, across eight everyday clinical areas."
        "</div>",
        unsafe_allow_html=True,
    )

    if len(kobo) == 0:
        st.info("No health-worker responses yet.")
        return

    rows = []
    for pre, post, label in F_DOMAINS:
        if pre in kobo.columns and post in kobo.columns:
            b = kobo[pre].mean()
            n = kobo[post].mean()
            rows.append({"label": label, "before_mean": b, "now_mean": n, "delta": n - b})
    if not rows:
        st.info("Confidence data not available.")
        return
    domain_df = pd.DataFrame(rows)

    # ---------------------------------------------------------------------
    # KPI row
    # ---------------------------------------------------------------------

    overall_before = domain_df["before_mean"].mean()
    overall_now = domain_df["now_mean"].mean()
    overall_delta = domain_df["delta"].mean()

    row = st.columns(3)
    with row[0]:
        st.metric("Confidence before (out of 5)", f"{overall_before:.1f}")
    with row[1]:
        st.metric("Confidence after (out of 5)", f"{overall_now:.1f}")
    with row[2]:
        st.metric("Average increase", f"+{overall_delta:.1f}")

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q12 — slopegraph
    # ---------------------------------------------------------------------

    st.markdown("#### Confidence before and after, by clinical area")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "Each line is one clinical area, connecting average confidence before the app to "
        "average confidence after. Lines sloping up mean health workers felt more confident. "
        "Hover over any line to see which area it is."
        "</div>",
        unsafe_allow_html=True,
    )

    slope_df = domain_df.sort_values("delta", ascending=False).reset_index(drop=True)
    top_mover = slope_df.iloc[0]["label"]  # biggest increase, drawn in ink

    fig_slope = go.Figure()
    for _, r in slope_df.iterrows():
        is_top = r["label"] == top_mover
        color = COLORS["primary"] if is_top else COLORS["muted"]
        width = 2.5 if is_top else 1.5
        fig_slope.add_trace(go.Scatter(
            x=["Before", "After"],
            y=[r["before_mean"], r["now_mean"]],
            mode="lines+markers",
            line=dict(color=color, width=width),
            marker=dict(size=7, color=color, line=dict(width=2, color="white")),
            hovertemplate=f"<b>{r['label']}</b><br>%{{x}}: %{{y:.1f}}<extra></extra>",
            showlegend=False,
        ))
        # Labels are shown on hover (lines bunch too tightly to label in place).
        # Only the single biggest mover is named directly, as a static anchor.
        if is_top:
            fig_slope.add_annotation(
                x="After", y=r["now_mean"], xshift=10, xanchor="left", yanchor="middle",
                text=f"{r['label']}  (biggest rise)", showarrow=False,
                font=dict(size=11, color=COLORS["primary"], weight=600),
            )

    # Tighten the y-range to the actual data span so endpoints spread out and
    # labels stop colliding. Padded slightly above/below the observed values.
    y_lo = min(slope_df["before_mean"].min(), slope_df["now_mean"].min())
    y_hi = max(slope_df["before_mean"].max(), slope_df["now_mean"].max())
    pad = 0.25
    fig_slope.update_layout(
        height=520,
        showlegend=False,
        xaxis=dict(showgrid=False, ticks="", range=[-0.15, 1.15],
                   tickfont=dict(size=13, color=COLORS["text_secondary"])),
        yaxis=dict(title="Average confidence (out of 5)",
                   range=[max(1, y_lo - pad), min(5, y_hi + pad)],
                   showgrid=True, gridcolor="#F1F5F9"),
        margin=dict(l=56, r=120, t=20, b=48),
    )
    st.plotly_chart(fig_slope, use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q13 — change per area
    # ---------------------------------------------------------------------

    st.markdown("#### How much confidence increased, by area")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "The size of the increase in average confidence for each clinical area."
        "</div>",
        unsafe_allow_html=True,
    )

    bar_df = domain_df.sort_values("delta", ascending=True).reset_index(drop=True)
    fig_delta = go.Figure()
    fig_delta.add_trace(go.Bar(
        y=bar_df["label"],
        x=bar_df["delta"],
        orientation="h",
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        customdata=bar_df[["before_mean", "now_mean"]].values,
        hovertemplate="<b>%{y}</b><br>Before: %{customdata[0]:.1f}<br>"
                      "After: %{customdata[1]:.1f}<br>Increase: %{x:+.1f}<extra></extra>",
    ))
    fig_delta.update_layout(
        height=max(360, 40 * len(bar_df) + 80),
        showlegend=False,
        bargap=0.45,
        xaxis=dict(title=dict(text="Increase in average confidence", standoff=12),
                   zeroline=False, showgrid=False, rangemode="tozero"),
        yaxis=dict(title="", automargin=True),
        margin=dict(l=24, r=24, t=20, b=56),
    )
    st.plotly_chart(fig_delta, use_container_width=True, config=PLOTLY_CONFIG)

    # ---------------------------------------------------------------------
    # Caveat — important and mandatory
    # ---------------------------------------------------------------------

    st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='border-left: 3px solid #E2E8F0; padding: 0.5rem 1rem;
                    color: #64748B; font-size: 0.875rem; line-height: 1.6;'>
        <strong style='color: #475569;'>How to read this</strong><br>
        Both the "before" and "after" ratings were given by health workers in the same
        interview at the end of the pilot, recalling how confident they felt earlier.
        This shows their <em>perceived</em> change in confidence, which is encouraging, but
        it is not a measured before-and-after test.
        </div>
        """,
        unsafe_allow_html=True,
    )
