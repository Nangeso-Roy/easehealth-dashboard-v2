"""Feasibility tab — Q1, Q4, Q5, Q6 (per finalized analysis map).

Q1: uptake / reliability funnel — trained -> used -> assessments saved.
Q4: inference-time distribution (technical feasibility — does it run).
Q5: inference time by device model.
Q6: workflow integration (Kobo Section D, self-reported).
Q2, Q3, Q7 are not built (see analysis map: dead by design).
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.plot_theme import COLORS, SEQUENCE, PLOTLY_CONFIG

# Workshop attendance — trained FHWs. Update when the attendance register is confirmed.
TRAINED = 205


def render(assessments, field_log, kobo):
    st.markdown("### Feasibility")
    st.markdown(
        "<div style='color: #64748B; margin-bottom: 1.5rem;'>"
        "Whether the app works in the field: how fast it produces guidance "
        "on the phones used, and whether health workers found it a good fit for their "
        "day-to-day work."
        "</div>",
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------------------
    # Q1 — Uptake / reliability funnel: trained -> used -> saved
    # ---------------------------------------------------------------------

    st.markdown("#### Uptake and capture funnel")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "From health workers trained, to those who used the app, to assessments that "
        "were successfully saved to the database."
        "</div>",
        unsafe_allow_html=True,
    )

    enrolled = len(kobo)                 # FHWs who used the app (Kobo respondents)
    saved = len(assessments)             # assessments persisted to the DB
    stages = ["Trained", "Used the app", "Assessments saved"]
    values = [TRAINED, enrolled, saved]

    fig_funnel = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textinfo="value+percent initial",
        marker=dict(color=[COLORS["muted"], SEQUENCE[2], COLORS["primary"]]),
        connector=dict(line=dict(color="#E2E8F0", width=1)),
        hovertemplate="<b>%{y}</b><br>%{x}<extra></extra>",
    ))
    fig_funnel.update_layout(
        height=300,
        margin=dict(l=24, r=24, t=12, b=24),
        showlegend=False,
    )
    st.plotly_chart(fig_funnel, use_container_width=True, config=PLOTLY_CONFIG)
    st.markdown(
        "<div style='color: #64748B; font-size: 0.8125rem; margin-top: -0.75rem;'>"
        f"<i>{TRAINED} trained at the launch workshop. {enrolled} went on to use the app "
        f"during the pilot. {saved} assessments persisted to the database; the gap reflects "
        f"assessments that did not save on a device still in active development.</i>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q4 — Inference time distribution (histogram)
    # ---------------------------------------------------------------------

    st.markdown("#### Inference time distribution")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "How long the app takes to produce its guidance after the health worker enters "
        "a patient's details. Each bar groups assessments into 20-second ranges."
        "</div>",
        unsafe_allow_html=True,
    )

    inf_secs = assessments["inference_ms"].dropna() / 1000

    if len(inf_secs) > 0:
        median_s = inf_secs.median()
        fig_inf = go.Figure()
        fig_inf.add_trace(go.Histogram(
            x=inf_secs,
            xbins=dict(size=20),
            marker=dict(color=COLORS["primary"], line=dict(width=0)),
            hovertemplate="<b>%{x} s</b><br>%{y} assessments<extra></extra>",
        ))
        fig_inf.add_vline(
            x=median_s, line=dict(color="#0F172A", width=1.5, dash="dot"),
            annotation_text=f"median {median_s:.0f}s",
            annotation_position="top right",
            annotation_font=dict(size=11, color="#475569"),
        )
        fig_inf.update_layout(
            height=300,
            showlegend=False,
            xaxis=dict(title="Inference time (seconds)", rangemode="tozero"),
            yaxis=dict(title="Assessments", rangemode="tozero"),
            bargap=0.05,
            margin=dict(l=48, r=24, t=12, b=48),
        )
        st.plotly_chart(fig_inf, use_container_width=True, config=PLOTLY_CONFIG)
        st.markdown(
            "<div style='color: #64748B; font-size: 0.8125rem; margin-top: -0.5rem;'>"
            f"<i>The app takes about {median_s:.0f} seconds on average to produce guidance, "
            "running entirely on the phone with no internet connection. "
            f"Based on {len(inf_secs)} assessments; {len(assessments) - len(inf_secs)} did not record a timing.</i>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("No inference latency data yet.")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q5 — Inference time by device model (box plot)
    # ---------------------------------------------------------------------

    st.markdown("#### Inference time by device model")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "The same timing, broken down by the phone model used. Most assessments ran on "
        "the two phones supplied for the pilot (Samsung A17 and A16)."
        "</div>",
        unsafe_allow_html=True,
    )

    by_device = assessments.dropna(subset=["device_model", "inference_ms"]).copy()
    by_device["inference_s"] = by_device["inference_ms"] / 1000

    if len(by_device) > 0:
        order = (
            by_device.groupby("device_model")["inference_s"]
            .median()
            .sort_values()
            .index.tolist()
        )
        # Friendly names for the two pilot phones; others kept as their model code.
        device_names = {"SM-A175F": "Samsung A17", "SM-A165F": "Samsung A16"}

        fig_dev = go.Figure()
        for model in order:
            sub = by_device[by_device["device_model"] == model]
            n = len(sub)
            disp = device_names.get(model, model)
            label = f"{disp} (n={n})"
            if n >= 5:
                fig_dev.add_trace(go.Box(
                    y=sub["inference_s"],
                    name=label,
                    marker=dict(color=COLORS["primary"]),
                    line=dict(color=COLORS["primary"], width=1.5),
                    fillcolor="rgba(15, 23, 42, 0.06)",
                    boxmean=False,
                    hovertemplate="<b>" + disp + "</b><br>%{y:.1f}s<extra></extra>",
                ))
            else:
                fig_dev.add_trace(go.Scatter(
                    y=sub["inference_s"],
                    x=[label] * n,
                    mode="markers",
                    marker=dict(color=COLORS["muted"], size=9,
                                line=dict(width=1, color="#FFFFFF")),
                    hovertemplate="<b>" + disp + "</b><br>%{y:.1f}s<extra></extra>",
                ))
        fig_dev.update_layout(
            height=320,
            showlegend=False,
            xaxis=dict(title=""),
            yaxis=dict(title="Inference time (seconds)", rangemode="tozero"),
            margin=dict(l=48, r=24, t=12, b=48),
        )
        st.plotly_chart(fig_dev, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.info("No device model data yet.")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Q6 — Workflow integration (Kobo Section D, coded 1-5)
    # ---------------------------------------------------------------------

    st.markdown("#### Workflow integration (self-reported)")
    st.markdown(
        "<div style='color: #64748B; font-size: 0.875rem; margin-top: -0.5rem;'>"
        "What health workers said about fitting the app into their daily work. Bars to the "
        "right of the centre line are agreement, bars to the left are disagreement. Items "
        "are ordered with the strongest agreement at the top."
        "</div>",
        unsafe_allow_html=True,
    )

    d_items = [
        ("d01_tech_speed", "Responded quickly enough"),
        ("d02_tech_reliable", "Worked reliably"),
        ("d03_tech_offline", "Offline functionality worked"),
        ("d04_wf_integrate", "Integrated into routine workflow"),
        ("d05_wf_time", "Did not slow consultations"),
        ("d06_wf_compat", "Compatible with my way of working"),
        ("d07_infra_device", "Smartphone was adequate"),
        ("d08_infra_battery", "Battery was sufficient"),
        ("d09_infra_space", "Adequate physical space"),
        ("d10_train_sufficient", "Training was sufficient"),
        ("d11_train_troubleshoot", "Prepared to troubleshoot"),
    ]
    d_cols = [(c, lbl) for c, lbl in d_items if c in kobo.columns]

    if d_cols:
        # Build per-item counts and a net-agreement score for ordering
        rows = []
        for col, lbl in d_cols:
            counts = {lvl: int((kobo[col] == lvl).sum()) for lvl in [1, 2, 3, 4, 5]}
            net = (counts[4] + counts[5]) - (counts[1] + counts[2])
            rows.append({"item": lbl, "net": net, **counts})
        ldf = pd.DataFrame(rows).sort_values("net", ascending=True).reset_index(drop=True)

        # Diverging layout: neutral straddles zero; disagree extends left, agree right.
        # Semantic palette: disagreement in the clinical-alert family, agreement in ink.
        seg_colors = {
            "Strongly disagree": "#B4452F",   # emergency
            "Disagree": "#D89A8E",            # lighter brick
            "Neutral": "#E2E8F0",             # hair
            "Agree": "#94A3B8",               # muted
            "Strongly agree": "#0F172A",      # ink
        }

        fig_d = go.Figure()
        # left side (disagree), drawn as negative values
        # order of stacking from centre outward
        for lvl, name, sign in [
            (3, "Neutral", "split_left"),
            (2, "Disagree", "neg"),
            (1, "Strongly disagree", "neg"),
        ]:
            if sign == "neg":
                x = [-ldf[lvl]] if False else [-v for v in ldf[lvl]]
            else:  # half of neutral to the left
                x = [-(v / 2) for v in ldf[3]]
            fig_d.add_trace(go.Bar(
                y=ldf["item"], x=x, name=name, orientation="h",
                marker=dict(color=seg_colors[name], line=dict(width=1.5, color="#FFFFFF")),
                hovertemplate="<b>%{y}</b><br>" + name + ": %{customdata}<extra></extra>",
                customdata=ldf[3] if sign == "split_left" else ldf[lvl],
                showlegend=(name != "Neutral"),
            ))
        # right side (agree), positive values
        for lvl, name, sign in [
            (3, "Neutral", "split_right"),
            (4, "Agree", "pos"),
            (5, "Strongly agree", "pos"),
        ]:
            if sign == "pos":
                x = list(ldf[lvl])
            else:  # other half of neutral to the right
                x = [v / 2 for v in ldf[3]]
            fig_d.add_trace(go.Bar(
                y=ldf["item"], x=x, name=name, orientation="h",
                marker=dict(color=seg_colors[name], line=dict(width=1.5, color="#FFFFFF")),
                hovertemplate="<b>%{y}</b><br>" + name + ": %{customdata}<extra></extra>",
                customdata=ldf[3] if sign == "split_right" else ldf[lvl],
                showlegend=(name == "Agree" or name == "Strongly agree"),
            ))

        fig_d.update_layout(
            height=max(440, 44 * len(d_cols) + 120),
            barmode="relative",
            bargap=0.5,
            xaxis=dict(title=dict(text="Health workers (disagree ◄ | ► agree)", standoff=12),
                       showgrid=False, zeroline=True, zerolinecolor="#94A3B8", zerolinewidth=1),
            yaxis=dict(title="", automargin=True, tickfont=dict(size=13, color="#475569")),
            legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="left", x=0,
                        font=dict(size=12, color="#64748B"), itemsizing="constant", tracegroupgap=6),
            margin=dict(l=24, r=24, t=64, b=56),
        )
        st.plotly_chart(fig_d, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.info("Workflow data not available.")

    # ---------------------------------------------------------------------
    # Notes
    # ---------------------------------------------------------------------

    st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='border-left: 3px solid #E2E8F0; padding: 0.5rem 1rem;
                    color: #64748B; font-size: 0.875rem; line-height: 1.6;'>
        <strong style='color: #475569;'>About this tab</strong><br>
        "Trained" is the number of health workers who attended the launch workshop.
        Timing is measured on the phone itself, with the app working fully offline.
        The workflow ratings come from interviews with the health workers who used the app.
        </div>
        """,
        unsafe_allow_html=True,
    )
