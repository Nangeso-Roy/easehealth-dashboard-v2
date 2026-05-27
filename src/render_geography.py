"""
Deployment-reach choropleth for the Snapshot page.

Renders all 13 Luwero ADM4 sub-counties as vector polygons (go.Choropleth),
auto-framed to fill the box (fitbounds), shaded on the unified ink ramp by
assessments per sub-county. Empty sub-counties stay visible as light neutral.

Place luwero_adm4.geojson in data/real/.
Requires subcounty_assessment_counts (see geography_loader.py).
"""

import json
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.plot_theme import PLOTLY_CONFIG, SEQ_SCALE


@st.cache_data
def _load_geojson(path):
    with open(path) as f:
        return json.load(f)


def render_geography(kobo_df, geojson_path=None, facility_col="facility_clean"):
    """
    kobo_df: the tagged Kobo dataframe (must contain `facility_col`).
    geojson_path: path to luwero_adm4.geojson (defaults to data/real/luwero_adm4.geojson).
    """
    from src.geography_loader import subcounty_assessment_counts

    if geojson_path is None:
        geojson_path = os.path.join("data", "real", "luwero_adm4.geojson")

    gj = _load_geojson(geojson_path)
    counts = subcounty_assessment_counts(kobo_df, facility_col=facility_col)

    rows = []
    for feat in gj["features"]:
        p = feat["properties"]
        name = p["adm4_name"]
        rows.append({
            "adm4_pcode": p["adm4_pcode"],
            "adm4_name": name,
            "assessments": int(counts.get(name, 0)),
        })
    df = pd.DataFrame(rows)

    total = int(df["assessments"].sum())
    active = int((df["assessments"] > 0).sum())

    # --- header ---
    st.markdown(
        "<div style='margin:0 0 0.35rem 0;'>"
        "<span style='font-size:1.05rem;font-weight:600;color:#0F172A;'>Deployment reach</span>"
        "<span style='font-size:0.85rem;color:#64748B;margin-left:0.6rem;'>"
        f"Where assessments happened, by sub-county &middot; {total} assessments across "
        f"{active} of 13 Luwero sub-counties"
        "</span></div>",
        unsafe_allow_html=True,
    )

    fig = go.Figure(go.Choropleth(
        geojson=gj,
        locations=df["adm4_pcode"],
        featureidkey="properties.adm4_pcode",
        z=df["assessments"],
        colorscale=SEQ_SCALE,
        zmin=0,
        marker_line_color="#FFFFFF",
        marker_line_width=1.0,
        customdata=df[["adm4_name"]].values,
        hovertemplate="<b>%{customdata[0]}</b><br>Assessments: %{z}<extra></extra>",
        colorbar=dict(
            title=dict(text="Assessments", font=dict(size=12, color="#475569"), side="right"),
            thickness=10, len=0.6, x=1.0, xpad=4,
            tickfont=dict(size=11, color="#64748B"),
            outlinewidth=0, ticks="outside", ticklen=3, tickcolor="#E2E8F0",
        ),
    ))

    # Auto-frame to the polygons so the district fills the box (no dead space).
    fig.update_geos(
        fitbounds="locations",
        visible=False,                 # no basemap graticule/coastlines
        projection_type="mercator",
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        height=440,
        margin={"r": 0, "t": 6, "l": 0, "b": 6},
        font=dict(family="Inter, sans-serif"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode=False,
    )

    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    st.caption(
        "This map counts every assessment recorded in the field by the sub-county of its "
        "facility, so it includes assessments that were not later saved to the database. "
        "The Snapshot total above counts only those saved to the database. Eight Luwero "
        "sub-counties were outside the pilot area and show no assessments."
    )
