"""
Custom Plotly template for the Ease Health dashboard.

ONE governed palette, three roles:
  1. Neutral magnitude  — ink / muted / hair  (default for almost every chart)
  2. One sequential ramp — seq                (maps + heatmaps only)
  3. Clinical semantics  — routine/urgent/emergency (triage, alerts only)

Colour encodes meaning, never identity. The page sits on a soft off-white
canvas (#F7F6F3); cards/charts are true white, giving gentle editorial depth.
"""

import plotly.graph_objects as go
import plotly.io as pio


# ---------------------------------------------------------------------------
# The governed palette
# ---------------------------------------------------------------------------

PALETTE = {
    # 1. NEUTRAL MAGNITUDE — the default language for nearly every chart
    "ink":    "#0F172A",   # focal / primary series
    "muted":  "#CBD5E1",   # everything that is NOT the focal series
    "hair":   "#E2E8F0",   # gridlines, borders, baselines

    # 2. ONE SEQUENTIAL RAMP — maps + heatmaps ONLY (single ink-family hue)
    "seq": ["#F1F5F9", "#CBD5E1", "#94A3B8", "#475569", "#0F172A"],

    # 3. CLINICAL SEMANTICS — referral urgency / red-flags / privacy flag ONLY
    "routine":   "#5B8C6E",  # muted green  — low / routine
    "urgent":    "#C99A3A",  # muted amber  — medium / urgent
    "emergency": "#B4452F",  # muted brick  — high / emergency / alert

    # Canvas + text
    "canvas":         "#F7F6F3",  # page background (soft off-white)
    "surface":        "#FFFFFF",  # cards / chart paper
    "text":           "#0F172A",
    "text_secondary": "#64748B",
    "text_tertiary":  "#94A3B8",
}

# Plotly sequential colorscale form (for go.Heatmap / choropleth colorscale=)
SEQ_SCALE = [[i / (len(PALETTE["seq"]) - 1), c] for i, c in enumerate(PALETTE["seq"])]


# ---------------------------------------------------------------------------
# Back-compat aliases — existing tab code references these names.
# They now point at the unified palette so older charts inherit the new system
# until each is migrated chart-by-chart.
# ---------------------------------------------------------------------------

COLORS = {
    "primary": PALETTE["ink"],
    "secondary": "#475569",
    "muted": PALETTE["muted"],
    "grid": "#F1F5F9",
    "hair": PALETTE["hair"],
    "text": PALETTE["text"],
    "text_secondary": PALETTE["text_secondary"],
    "background": PALETTE["surface"],
    # semantic aliases (amber kept for any legacy reference, now the 'urgent' hue)
    "accent_amber": PALETTE["urgent"],
    "routine": PALETTE["routine"],
    "urgent": PALETTE["urgent"],
    "emergency": PALETTE["emergency"],
    "neutral_lt": PALETTE["text_tertiary"],
}

# Legacy categorical sequence — now an ink-family ramp, NOT a rainbow.
# (Charts should prefer series_colors(); this remains only so old calls degrade
# gracefully to neutral tones instead of clown colours.)
SEQUENCE = [
    PALETTE["ink"], "#334155", "#475569", "#64748B",
    "#94A3B8", "#CBD5E1", "#334155", "#475569",
]


# ---------------------------------------------------------------------------
# Highlight-one helper — use wherever bars/series share one meaning
# ---------------------------------------------------------------------------

def series_colors(labels, focal=None):
    """ink for the focal category, muted for the rest. focal=None -> all ink."""
    if focal is None:
        return [PALETTE["ink"]] * len(labels)
    return [PALETTE["ink"] if l == focal else PALETTE["muted"] for l in labels]


def triage_colors(labels):
    """Map triage/urgency labels to the clinical-semantic trio."""
    m = {
        "Emergency referral": PALETTE["emergency"],
        "Urgent clinic visit": PALETTE["urgent"],
        "Routine care": PALETTE["routine"],
    }
    return [m.get(l, PALETTE["muted"]) for l in labels]


# ---------------------------------------------------------------------------
# Plotly template
# ---------------------------------------------------------------------------

def _build_template():
    layout = go.Layout(
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            size=13,
            color=PALETTE["text"],
        ),
        title=dict(
            font=dict(size=16, color=PALETTE["text"], weight=600),
            x=0, xanchor="left", pad=dict(t=8, b=12),
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        colorway=SEQUENCE,
        margin=dict(l=48, r=24, t=48, b=48),
        xaxis=dict(
            showgrid=False, zeroline=False, showline=True,
            linecolor=PALETTE["hair"],
            tickfont=dict(size=12, color=PALETTE["text_secondary"]),
            title=dict(font=dict(size=12, color=PALETTE["text_secondary"]), standoff=10),
            ticks="outside", tickcolor=PALETTE["hair"], ticklen=4,
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#F1F5F9", gridwidth=1,
            zeroline=False, showline=False,
            tickfont=dict(size=12, color=PALETTE["text_secondary"]),
            title=dict(font=dict(size=12, color=PALETTE["text_secondary"]), standoff=10),
            ticks="",
        ),
        legend=dict(
            font=dict(size=12, color=PALETTE["text_secondary"]),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
        ),
        hoverlabel=dict(
            bgcolor=PALETTE["text"], bordercolor=PALETTE["text"],
            font=dict(family="Inter, sans-serif", size=12, color="#FFFFFF"),
        ),
    )
    return go.layout.Template(layout=layout)


def register():
    """Register the custom template and set it as default. Call at app start."""
    pio.templates["easehealth"] = _build_template()
    pio.templates.default = "easehealth"


# ---------------------------------------------------------------------------
# Streamlit-Plotly config — hides default chrome on every chart
# ---------------------------------------------------------------------------

PLOTLY_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": False,
    "doubleClick": False,
    "showAxisDragHandles": False,
    "showAxisRangeEntryBoxes": False,
}
