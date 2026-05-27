"""Acceptability tab — Q8, Q9, Q10, Q11 (per finalized analysis map).

Q8: usability score (SUS) distribution + by cadre.
Q9: overall acceptability + acceptability composite.
Q10: willingness to continue / recommend.
Q11: acceptability by subgroup (exploratory; small cells flagged).
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.plot_theme import COLORS, SEQUENCE, PLOTLY_CONFIG


def render(assessments, field_log, kobo):
    st.markdown("### Acceptability")
    st.markdown(
        "<div style='color: #64748B; margin-bottom: 1.5rem;'>"
        "How the health workers received the app: how easy it was to use, how satisfied "
        "they were, and whether they would keep using it and recommend it."
        "</div>",
        unsafe_allow_html=True,
    )

    if len(kobo) == 0:
        st.info("No health-worker responses yet.")
        return

    sus = kobo["sus_score"].dropna() if "sus_score" in kobo.columns else pd.Series(dtype=float)
    mean_sus = sus.mean() if len(sus) > 0 else None
    prop_above_68 = (sus >= 68).mean() if len(sus) > 0 else None
    prop_good_plus = (kobo["e12_overall"] >= 4).mean() if "e12_overall" in kobo.columns else None

    # ---------------------------------------------------------------------
    # Top row — three KPI tiles
    # ---------------------------------------------------------------------

    row = st.columns(3)
    with row[0]:
        st.metric("Average ease-of-use score", f"{mean_sus:.0f} / 100" if mean_sus is not None else "—")
    with row[1]:
        st.metric(
            "Rated the app easy to use",
            f"{prop_above_68 * 100:.0f}%" if prop_above_68 is not None else "—",
        )
    with row[2]:
        st.metric(
            "Rated overall experience good or better",
            f"{prop_good_plus * 100:.0f}%" if prop_good_plus is not None else "—",
        )

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q8 — usability score distribution
    # ---------------------------------------------------------------------

    st.markdown("#### Ease-of-use scores")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "A standard 0 to 100 ease-of-use score from each health worker. The dashed line at "
        "68 is the level most apps are expected to reach."
        "</div>",
        unsafe_allow_html=True,
    )

    if len(sus) > 0:
        fig_sus = go.Figure()
        fig_sus.add_trace(go.Histogram(
            x=sus,
            xbins=dict(size=5, start=0, end=100),
            marker=dict(color=COLORS["primary"], line=dict(width=1.5, color="#FAFAF9")),
            hovertemplate="<b>Score %{x}</b><br>%{y} health workers<extra></extra>",
        ))
        fig_sus.add_vline(
            x=68,
            line=dict(color=COLORS["accent_amber"], width=1.5, dash="dot"),
            annotation_text="expected level (68)",
            annotation_position="top right",
            annotation_font=dict(size=11, color=COLORS["accent_amber"]),
        )
        fig_sus.update_layout(
            height=320,
            showlegend=False,
            xaxis=dict(title=dict(text="Ease-of-use score (0 to 100)", standoff=12),
                       range=[0, 100], showgrid=False, zeroline=False),
            yaxis=dict(title="Health workers", rangemode="tozero"),
            bargap=0.05,
            margin=dict(l=48, r=24, t=12, b=56),
        )
        st.plotly_chart(fig_sus, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown(
            "<div style='color: #64748B; font-size: 0.8125rem; margin-top: -0.5rem;'>"
            f"<i>Average score: {mean_sus:.0f} out of 100.</i></div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("No ease-of-use scores available.")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q8b — usability by cadre
    # ---------------------------------------------------------------------

    st.markdown("#### Ease-of-use by health-worker type")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "How ease-of-use scores varied across different types of health worker."
        "</div>",
        unsafe_allow_html=True,
    )

    if "a04_cadre_label" in kobo.columns and len(sus) > 0:
        sub = kobo.dropna(subset=["a04_cadre_label", "sus_score"]).copy()
        order = sub.groupby("a04_cadre_label")["sus_score"].median().sort_values().index.tolist()

        fig_cadre = go.Figure()
        for cadre in order:
            cadre_data = sub[sub["a04_cadre_label"] == cadre]
            n = len(cadre_data)
            label = f"{cadre} (n={n})"
            if n >= 5:
                # enough points to show a distribution
                fig_cadre.add_trace(go.Box(
                    y=cadre_data["sus_score"],
                    name=label,
                    marker=dict(color=COLORS["primary"]),
                    line=dict(color=COLORS["primary"], width=1.5),
                    fillcolor="rgba(15, 23, 42, 0.06)",
                    boxpoints="outliers",
                    hovertemplate="<b>" + cadre + "</b><br>Score: %{y}<extra></extra>",
                ))
            else:
                # too few to imply a distribution: show the individual points only
                fig_cadre.add_trace(go.Scatter(
                    y=cadre_data["sus_score"],
                    x=[label] * n,
                    mode="markers",
                    marker=dict(color=COLORS["muted"], size=9,
                                line=dict(width=1, color="#FFFFFF")),
                    hovertemplate="<b>" + cadre + "</b><br>Score: %{y}<extra></extra>",
                ))
        fig_cadre.add_hline(
            y=68, line=dict(color=COLORS["accent_amber"], width=1, dash="dot"),
            annotation_text="68", annotation_position="right",
            annotation_font=dict(size=10, color=COLORS["accent_amber"]),
        )
        fig_cadre.update_layout(
            height=380,
            showlegend=False,
            xaxis=dict(title="", showgrid=False, tickangle=-20),
            yaxis=dict(title="Ease-of-use score", range=[0, 100]),
            margin=dict(l=48, r=24, t=12, b=96),
        )
        st.plotly_chart(fig_cadre, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown(
            "<div style='color: #64748B; font-size: 0.8125rem; margin-top: -0.5rem;'>"
            "<i>Counts (n) shown per group; smaller groups should be read with caution.</i></div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("Health-worker type or score data missing.")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q10 — willingness to continue / recommend
    # ---------------------------------------------------------------------

    st.markdown("#### Would they keep using it, and recommend it?")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "Share of health workers who agreed they would continue using the app, and would "
        "recommend it to a colleague."
        "</div>",
        unsafe_allow_html=True,
    )

    cols_q10 = st.columns(2)

    def _agreement_donut(series, title):
        n_total = series.notna().sum()
        n_agree = (series >= 4).sum()
        n_other = n_total - n_agree
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=["Agree / Strongly agree", "Other"],
            values=[n_agree, n_other],
            hole=0.65,
            marker=dict(colors=[COLORS["primary"], "#E2E8F0"], line=dict(color="#FAFAF9", width=2)),
            sort=False, direction="clockwise", textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} health workers<extra></extra>",
        ))
        pct = (n_agree / n_total * 100) if n_total > 0 else 0
        fig.add_annotation(text=f"<b style='font-size:28px;color:{COLORS['primary']};'>{pct:.0f}%</b>",
                           showarrow=False, x=0.5, y=0.55, xref="paper", yref="paper", font=dict(family="Inter"))
        fig.add_annotation(text=f"<span style='font-size:12px;color:{COLORS['text_secondary']};'>{title}</span>",
                           showarrow=False, x=0.5, y=0.40, xref="paper", yref="paper", font=dict(family="Inter"))
        fig.update_layout(height=260, showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
        return fig

    with cols_q10[0]:
        if "e07_willing1" in kobo.columns:
            st.plotly_chart(_agreement_donut(kobo["e07_willing1"], "would continue"),
                            use_container_width=True, config=PLOTLY_CONFIG)
    with cols_q10[1]:
        if "e08_willing2" in kobo.columns:
            st.plotly_chart(_agreement_donut(kobo["e08_willing2"], "would recommend"),
                            use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q11 — acceptability by subgroup (exploratory)
    # ---------------------------------------------------------------------

    st.markdown("#### How acceptance varied across health workers")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "Average overall acceptance (1 to 5) within each group. Exploratory. Smaller groups "
        "are less reliable."
        "</div>",
        unsafe_allow_html=True,
    )

    if "acceptability_mean" not in kobo.columns:
        st.info("Acceptance data not available.")
        return

    cols_q11 = st.columns(2)

    def _subgroup_bar(group_col, title, ax_col, min_n=5):
        if group_col not in kobo.columns:
            with ax_col:
                st.info(f"{title}: data missing.")
            return
        sub = kobo.dropna(subset=[group_col, "acceptability_mean"])
        grp = sub.groupby(group_col)["acceptability_mean"].agg(["mean", "count"])
        grp = grp[grp["count"] >= min_n].sort_values("mean")  # suppress tiny cells
        if len(grp) == 0:
            with ax_col:
                st.info(f"{title}: groups too small to show.")
            return
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=[f"{idx} (n={int(r['count'])})" for idx, r in grp.iterrows()],
            x=grp["mean"].values,
            orientation="h",
            marker=dict(color=COLORS["primary"], line=dict(width=0)),
            hovertemplate="<b>%{y}</b><br>%{x:.2f} / 5<extra></extra>",
        ))
        fig.update_layout(
            height=260, showlegend=False,
            xaxis=dict(title="", range=[1, 5], showgrid=False),
            yaxis=dict(title="", automargin=True),
            bargap=0.45, margin=dict(l=12, r=24, t=36, b=32),
            title=dict(text=title, font=dict(size=13, color=COLORS["text_secondary"]),
                       x=0, xanchor="left", y=0.97, yanchor="top"),
        )
        with ax_col:
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    _subgroup_bar("a04_cadre_label", "By health-worker type", cols_q11[0])
    _subgroup_bar("a09_digital_skill_label", "By smartphone skill", cols_q11[1])

    st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='border-left: 3px solid #E2E8F0; padding: 0.5rem 1rem;
                    color: #64748B; font-size: 0.875rem; line-height: 1.6;'>
        <strong style='color: #475569;'>About this tab</strong><br>
        The ease-of-use score is a widely-used 0 to 100 measure built from ten standard
        questions. All ratings come from interviews with the health workers who used the app.
        Subgroup breakdowns are exploratory and groups smaller than five are not shown.
        </div>
        """,
        unsafe_allow_html=True,
    )
