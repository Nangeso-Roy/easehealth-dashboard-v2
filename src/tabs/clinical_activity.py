"""Clinical Activity tab — Q20, Q21, Q22 (per finalized analysis map).

Q20: most common conditions + conditions by health-worker type.
Q21: how often the app flagged a patient for referral (from triage level).
Q22: whether the app's guidance was used (with capture-gap framing).
All from app data (the saved assessments).
"""

import re
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.plot_theme import COLORS, SEQUENCE, PLOTLY_CONFIG, SEQ_SCALE, triage_colors


def _group_condition(text):
    """Light, transparent grouping of the free-text condition field."""
    if not isinstance(text, str) or not text.strip():
        return None
    t = text.lower()
    if "malaria" in t:
        return "Malaria (all forms)"
    if "pneumonia" in t:
        return "Pneumonia"
    if "diarrhoea" in t or "diarrhea" in t:
        return "Diarrhoea"
    if "meningitis" in t:
        return "Meningitis"
    if "cold" in t or "rhinitis" in t or "uri" in t:
        return "Common cold / URTI"
    # otherwise keep the original (trimmed) label
    return text.strip()[:48]


def render(assessments, field_log, kobo):
    st.markdown("### Clinical Activity")
    st.markdown(
        "<div style='color: #64748B; margin-bottom: 1.5rem;'>"
        "What the app was used for in the field: the conditions it assessed, "
        "how often it flagged patients for referral, and whether its guidance was used."
        "</div>",
        unsafe_allow_html=True,
    )

    if len(assessments) == 0:
        st.info("No assessments yet.")
        return

    a = assessments.copy()
    # Use the shared canonical grouping (same as Snapshot) for consistency.
    a["condition_group"] = a["condition_canonical"]

    # ---------------------------------------------------------------------
    # Q20 — top conditions
    # ---------------------------------------------------------------------

    st.markdown("#### Most common conditions assessed")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "The conditions the app most often produced guidance for."
        "</div>",
        unsafe_allow_html=True,
    )

    counts = a["condition_group"].value_counts()
    if len(counts) > 0:
        top = counts.head(5).sort_values()  # show the five most common
        n_single = int((counts == 1).sum())

        fig_cond = go.Figure(go.Bar(
            y=top.index, x=top.values, orientation="h",
            marker=dict(color=COLORS["primary"], line=dict(width=0)),
            hovertemplate="<b>%{y}</b><br>%{x} assessments<extra></extra>",
        ))
        fig_cond.update_layout(
            height=max(260, 40 * len(top) + 80),
            showlegend=False,
            xaxis=dict(title="Assessments", rangemode="tozero", showgrid=False),
            yaxis=dict(title="", automargin=True),
            bargap=0.4, margin=dict(l=24, r=24, t=12, b=48),
        )
        st.plotly_chart(fig_cond, use_container_width=True, config=PLOTLY_CONFIG)
        if n_single > 0:
            st.markdown(
                "<div style='color: #64748B; font-size: 0.8125rem; margin-top: -0.5rem;'>"
                f"<i>Showing the five most common. A further {n_single} conditions were each "
                "recorded only once.</i></div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No condition data.")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q20b — condition by health-worker type (heatmap, exploratory)
    # ---------------------------------------------------------------------

    st.markdown("#### Conditions by health-worker type")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "Which types of health worker assessed which conditions. This shows the most "
        "common conditions only, so the cells do not add up to all 81 assessments."
        "</div>",
        unsafe_allow_html=True,
    )

    sub = a.dropna(subset=["condition_group", "role"])
    if len(sub) > 0:
        top_conds = sub["condition_group"].value_counts().head(3).index.tolist()
        sub2 = sub[sub["condition_group"].isin(top_conds)]
        pivot = pd.crosstab(sub2["condition_group"], sub2["role"])
        zmax = pivot.values.max() if pivot.values.size else 1

        # per-cell text colour: white on dark cells, dark on light cells
        annotations = []
        ys = list(pivot.index)
        xs = list(pivot.columns)
        for i, yv in enumerate(ys):
            for j, xv in enumerate(xs):
                v = int(pivot.values[i][j])
                txt_color = "#FFFFFF" if (zmax and v / zmax >= 0.55) else "#0F172A"
                annotations.append(dict(x=xv, y=yv, text=str(v), showarrow=False,
                                        font=dict(size=12, color=txt_color, family="Inter")))

        fig_hm = go.Figure(go.Heatmap(
            z=pivot.values, x=xs, y=ys,
            colorscale=SEQ_SCALE,
            hovertemplate="<b>%{y}</b><br>%{x}: %{z}<extra></extra>",
            colorbar=dict(thickness=12, len=0.7, tickfont=dict(size=11, color="#64748B"), outlinewidth=0),
        ))
        fig_hm.update_layout(
            height=360,
            annotations=annotations,
            xaxis=dict(tickfont=dict(size=11, color=COLORS["text_secondary"]), tickangle=-15),
            yaxis=dict(automargin=True, tickfont=dict(size=11, color=COLORS["text_secondary"])),
            margin=dict(l=24, r=24, t=12, b=60),
        )
        st.plotly_chart(fig_hm, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.info("Not enough data for the breakdown.")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q21 — referral rate (from triage level)
    # ---------------------------------------------------------------------

    st.markdown("#### How often the app flagged a referral")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "Based on the urgency level the app assigned to each patient."
        "</div>",
        unsafe_allow_html=True,
    )

    if "triage_level" in a.columns:
        tri = a["triage_level"].value_counts()
        # plain ordering
        order = ["Emergency referral", "Urgent clinic visit", "Routine care"]
        tri = tri.reindex([o for o in order if o in tri.index])
        n_emerg = int(tri.get("Emergency referral", 0))
        pct_emerg = n_emerg / len(a) * 100

        fig_tri = go.Figure(go.Bar(
            x=tri.index, y=tri.values,
            marker=dict(color=triage_colors(list(tri.index))),
            hovertemplate="<b>%{x}</b><br>%{y} assessments<extra></extra>",
        ))
        fig_tri.update_layout(
            height=300, showlegend=False,
            xaxis=dict(title="", showgrid=False),
            yaxis=dict(title="Assessments", rangemode="tozero"),
            bargap=0.45, margin=dict(l=48, r=24, t=12, b=48),
        )
        st.plotly_chart(fig_tri, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown(
            "<div style='color: #64748B; font-size: 0.8125rem; margin-top: -0.5rem;'>"
            f"<i>The app flagged {n_emerg} of {len(a)} patients ({pct_emerg:.0f}%) for emergency "
            "referral.</i></div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("No urgency data.")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q22 — guidance used (capture-gap framing)
    # ---------------------------------------------------------------------

    st.markdown("#### Was the app's guidance used?")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "Whether the health worker recorded using the app's guidance. This was an optional "
        "field that was often left blank, so most assessments are \"not recorded\"."
        "</div>",
        unsafe_allow_html=True,
    )

    if "guidance_used" in a.columns:
        g = a["guidance_used"].fillna("Not recorded").replace("", "Not recorded")
        raw = g.value_counts()
        total_g = int(raw.sum())

        # Deliberate, fixed order and an on-palette magnitude ramp (no scattered labels)
        order = ["Yes", "Partially", "No", "Not recorded"]
        display = {"Yes": "Used", "Partially": "Partly used",
                   "No": "Not used", "Not recorded": "Not recorded"}
        palette = {"Used": "#0F172A", "Partly used": "#64748B",
                   "Not used": "#94A3B8", "Not recorded": "#E2E8F0"}

        labels, values, colors = [], [], []
        for key in order:
            if key in raw.index:
                lbl = display[key]
                labels.append(f"{lbl} ({int(raw[key])})")
                values.append(int(raw[key]))
                colors.append(palette[lbl])

        not_rec = int(raw.get("Not recorded", 0))
        pct_not_rec = (not_rec / total_g * 100) if total_g else 0

        fig_g = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.62,
            marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
            sort=False, direction="clockwise",
            textinfo="none",  # no scattered on-slice text; use the legend instead
            hovertemplate="<b>%{label}</b><extra></extra>",
        ))
        # Center stat: the honest headline is the missingness
        fig_g.add_annotation(
            text=f"<span style='font-family:Newsreader,serif;font-size:30px;color:#0F172A;'>"
                 f"{pct_not_rec:.0f}%</span>",
            showarrow=False, x=0.5, y=0.54, xref="paper", yref="paper",
        )
        fig_g.add_annotation(
            text="<span style='font-size:12px;color:#64748B;'>not recorded</span>",
            showarrow=False, x=0.5, y=0.40, xref="paper", yref="paper",
        )
        fig_g.update_layout(
            height=340,
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0,
                        font=dict(size=12, color="#475569")),
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig_g, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.info("No guidance-use data.")

    st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='border-left: 3px solid #E2E8F0; padding: 0.5rem 1rem;
                    color: #64748B; font-size: 0.875rem; line-height: 1.6;'>
        <strong style='color: #475569;'>About this tab</strong><br>
        These figures come from the assessments saved by the app. Condition names are
        grouped lightly (for example, all forms of malaria are counted together).
        Some optional fields, such as whether guidance was used, were often left blank,
        and this is shown honestly rather than hidden.
        </div>
        """,
        unsafe_allow_html=True,
    )
