"""Safety & AI Quality tab — Q23, Q24 (per finalized analysis map).

Q23: how often the privacy safety-net flagged possible personal information.
Q24: the app's confidence by urgency level + whether it takes longer on complex cases.
The override-pattern heatmap is intentionally not built (relies on the mostly-blank
guidance-used field).
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.plot_theme import COLORS, SEQUENCE, PLOTLY_CONFIG


def render(assessments, field_log, kobo):
    st.markdown("### Safety & AI Quality")
    st.markdown(
        "<div style='color: #64748B; margin-bottom: 1.5rem;'>"
        "Signals about how safely and sensibly the app behaved: its privacy safety-net, "
        "how confident it was across different urgency levels, and whether harder cases "
        "took it longer."
        "</div>",
        unsafe_allow_html=True,
    )

    if len(assessments) == 0:
        st.info("No assessments yet.")
        return

    a = assessments.copy()

    # ---------------------------------------------------------------------
    # Q23 — privacy safety-net flag rate
    # ---------------------------------------------------------------------

    st.markdown("#### Privacy safety-net")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "The app automatically scans entries for possible personal information (like a "
        "name). This shows how often that check was triggered, a sign the safety-net is "
        "working, not that information was exposed."
        "</div>",
        unsafe_allow_html=True,
    )

    if "ner_flagged" in a.columns:
        flagged = int(a["ner_flagged"].sum()) if a["ner_flagged"].dtype == bool \
            else int((a["ner_flagged"] == True).sum())
        total = len(a)
        not_flagged = total - flagged
        pct = flagged / total * 100 if total else 0

        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("Entries flagged for review", f"{flagged}")
            st.markdown(
                f"<div style='color:#64748B;font-size:0.8125rem;margin-top:-0.5rem;'>"
                f"<i>{pct:.0f}% of {total} assessments</i></div>",
                unsafe_allow_html=True,
            )
        with c2:
            fig_ner = go.Figure(go.Bar(
                x=[flagged, not_flagged],
                y=["Flagged for review", "No flag"],
                orientation="h",
                marker=dict(color=[COLORS["primary"], COLORS["muted"]]),
                hovertemplate="<b>%{y}</b><br>%{x} assessments<extra></extra>",
            ))
            fig_ner.update_layout(
                height=180, showlegend=False,
                xaxis=dict(title="Assessments", rangemode="tozero", showgrid=False),
                yaxis=dict(title="", automargin=True),
                bargap=0.4, margin=dict(l=24, r=24, t=8, b=40),
            )
            st.plotly_chart(fig_ner, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.info("No safety-net data.")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q24a — confidence by urgency level (stacked bar)
    # ---------------------------------------------------------------------

    st.markdown("#### The app's confidence, by how urgent the case was")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "How sure the app was about its guidance, broken down by the urgency it assigned. "
        "You would hope it is not over-confident on the most urgent cases."
        "</div>",
        unsafe_allow_html=True,
    )

    if "confidence" in a.columns and "triage_level" in a.columns:
        sub = a.dropna(subset=["confidence", "triage_level"]).copy()
        sub["confidence"] = sub["confidence"].str.capitalize()
        tri_order = ["Emergency referral", "Urgent clinic visit", "Routine care"]
        tri_order = [t for t in tri_order if t in sub["triage_level"].unique()]
        conf_levels = ["High", "Medium", "Low"]
        # Confidence is a magnitude, not a clinical alert: use the neutral ink ramp
        # (darker = more confident), not the urgency trio.
        conf_colors = {"High": "#0F172A", "Medium": "#94A3B8", "Low": "#CBD5E1"}

        fig_ct = go.Figure()
        for cl in conf_levels:
            counts = [int(((sub["triage_level"] == t) & (sub["confidence"] == cl)).sum())
                      for t in tri_order]
            fig_ct.add_trace(go.Bar(
                x=tri_order, y=counts, name=cl,
                marker=dict(color=conf_colors[cl], line=dict(width=1.5, color="#FAFAF9")),
                hovertemplate="<b>%{x}</b><br>" + cl + " confidence: %{y}<extra></extra>",
            ))
        fig_ct.update_layout(
            height=320, barmode="stack",
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0,
                        font=dict(size=12, color="#64748B")),
            xaxis=dict(title="", showgrid=False),
            yaxis=dict(title="Assessments", rangemode="tozero"),
            bargap=0.45, margin=dict(l=48, r=24, t=48, b=48),
        )
        st.plotly_chart(fig_ct, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.info("No confidence or urgency data.")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q24b — does the app take longer on more complex cases?
    # ---------------------------------------------------------------------

    st.markdown("#### Does the app take longer on more complex cases?")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "Each dot is one assessment: how much the health worker typed about the patient "
        "(a rough stand-in for case complexity) against how long the app took."
        "</div>",
        unsafe_allow_html=True,
    )

    sub = a.dropna(subset=["inference_ms", "symptoms_len"]).copy()
    sub["symptom_len"] = pd.to_numeric(sub["symptoms_len"], errors="coerce")
    sub = sub[sub["symptom_len"] > 0]
    if len(sub) > 0:
        sub["inference_s"] = sub["inference_ms"] / 1000
        fig_sc = go.Figure(go.Scatter(
            x=sub["symptom_len"], y=sub["inference_s"],
            mode="markers",
            marker=dict(size=9, color=COLORS["primary"], opacity=0.55,
                        line=dict(width=1, color="#FAFAF9")),
            hovertemplate="Detail entered: %{x} characters<br>Time: %{y:.0f}s<extra></extra>",
        ))
        fig_sc.update_layout(
            height=340, showlegend=False,
            xaxis=dict(title="Amount of patient detail entered (characters)",
                       rangemode="tozero", showgrid=False),
            yaxis=dict(title="Time to produce guidance (seconds)", rangemode="tozero"),
            margin=dict(l=56, r=24, t=12, b=52),
        )
        st.plotly_chart(fig_sc, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown(
            "<div style='color: #64748B; font-size: 0.8125rem; margin-top: -0.5rem;'>"
            "<i>Exploratory. The amount typed is only a rough proxy for how complex a case is.</i>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("Not enough data for this view.")

    st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='border-left: 3px solid #E2E8F0; padding: 0.5rem 1rem;
                    color: #64748B; font-size: 0.875rem; line-height: 1.6;'>
        <strong style='color: #475569;'>About this tab</strong><br>
        A flag from the privacy safety-net means the app caught possible personal
        information for review. It does not mean information was shared. The complexity
        view is exploratory: the amount a health worker typed is only a rough stand-in for
        how complicated a case was.
        </div>
        """,
        unsafe_allow_html=True,
    )
