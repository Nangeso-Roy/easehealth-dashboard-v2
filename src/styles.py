"""
Custom CSS injected into the Streamlit app.

Handles: the soft off-white canvas (white cards float on it for depth),
typography (Inter for UI, a display serif for hero numbers), layout density,
card styling, and removal of Streamlit's default chrome / auto-anchor icons.
"""

import streamlit as st


CUSTOM_CSS = """
<style>
/* ---------- Fonts ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&display=swap');

html, body, [class*="st"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* ---------- Soft canvas: page is a hair darker than the cards ---------- */
.stApp {
    background: #F7F6F3;
}

/* ---------- Hide default Streamlit chrome ---------- */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* Kill Streamlit's auto-anchor link icons next to headings */
[data-testid="stHeaderActionElements"] { display: none !important; }
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; }

/* ---------- Page padding & max width ---------- */
.block-container {
    padding-top: 2.5rem;
    padding-bottom: 4rem;
    padding-left: 3rem;
    padding-right: 3rem;
    max-width: 1400px;
}

/* ---------- Headings ---------- */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    letter-spacing: -0.02em;
    color: #0F172A;
}

h1 { font-size: 2rem; margin-bottom: 0.25rem; }
h2 { font-size: 1.4rem; margin-top: 2rem; margin-bottom: 1rem; padding-top: 0.5rem; }
h3 { font-size: 1.1rem; margin-top: 1.5rem; margin-bottom: 0.75rem; }

/* ---------- Body text ---------- */
p, .stMarkdown {
    color: #475569;
    line-height: 1.6;
}

/* ---------- Metric cards (st.metric) ---------- */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E7E5DF;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

[data-testid="stMetric"]:hover {
    border-color: #CBD5E1;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
}

[data-testid="stMetricLabel"] {
    font-size: 0.8125rem;
    font-weight: 500;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.25rem;
}

/* Hero numbers in the display serif, with tabular figures — reads editorial */
[data-testid="stMetricValue"] {
    font-family: 'Newsreader', Georgia, serif;
    font-size: 2.25rem;
    font-weight: 500;
    color: #0F172A;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
}

[data-testid="stMetricDelta"] {
    font-size: 0.8125rem;
    font-weight: 500;
    color: #64748B;
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 1px solid #E2E8F0;
    margin-bottom: 2rem;
}

.stTabs [data-baseweb="tab"] {
    height: 2.5rem;
    padding: 0 1rem;
    font-size: 0.9375rem;
    font-weight: 500;
    color: #64748B;
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0;
    transition: color 0.15s, border-color 0.15s;
}

.stTabs [data-baseweb="tab"]:hover { color: #0F172A; }

.stTabs [aria-selected="true"] {
    color: #0F172A;
    border-bottom: 2px solid #0F172A;
    background: transparent;
}

/* ---------- Plotly chart container — white card on the canvas ---------- */
.js-plotly-plot {
    border: 1px solid #E7E5DF;
    border-radius: 12px;
    padding: 0.75rem;
    background: #FFFFFF;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}

/* ---------- Dividers ---------- */
hr {
    border: none;
    border-top: 1px solid #E2E8F0;
    margin: 2rem 0;
}

/* ---------- Dataframe / table ---------- */
.stDataFrame {
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    overflow: hidden;
}

/* ---------- Expander (used for the analyst-only correlation matrix) ---------- */
.stExpander {
    border: 1px solid #E7E5DF;
    border-radius: 12px;
    background: #FFFFFF;
}

/* ---------- Print: drop app chrome so PDF exports read as a report ---------- */
@media print {
    header, footer, #MainMenu, [data-testid="stToolbar"] { display: none !important; }
    .stApp { background: #FFFFFF; }
    .block-container { padding-top: 0; }
    .js-plotly-plot { box-shadow: none; }
}
</style>
"""


def inject():
    """Inject the custom CSS into the Streamlit page. Call once at app start."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
