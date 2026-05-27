# Ease Health Pilot Dashboard

A descriptive, at-a-glance dashboard for the Ease Health pilot (Luwero District,
Uganda). Built with Streamlit and Plotly. It presents pilot results across seven
views: Snapshot, Feasibility, Acceptability, Clinical Confidence, Adoption,
Clinical Activity, and Safety & AI Quality.

This repository contains **code only**. No pilot data is included. Data files are
shared separately through a secure channel and must be placed in `data/real/`
before the app will run (see "Data files" below).

## Requirements

- Python 3.11+
- The packages in `requirements.txt`

## Setup

```bash
# 1. Create and activate an environment (example with conda)
conda create -n easehealth python=3.11 -y
conda activate easehealth

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add the data files (see below) into data/real/

# 4. Run
streamlit run app.py
```

## Data files

The app reads three files from `data/real/` (this folder is git-ignored and ships
empty). Obtain these through the secure channel, not from this repository:

| File                   | What it is                                            |
|------------------------|-------------------------------------------------------|
| `tier1_redacted.csv`   | Assessment records, PII-removed (see "Redaction")     |
| `kobo_tagged.xlsx`     | Health-worker survey responses, coded and facility-tagged |
| `luwero_adm4.geojson`  | Luwero sub-county boundaries (UBOS ADM4)              |

Without these files the app will raise a `FileNotFoundError` on start.

## Redaction (preparing data for sharing / deployment)

Raw database pulls contain identifiable fields and must never be committed or
deployed as-is. `make_redacted_data.py` produces a safe copy that keeps only the
columns the dashboard uses and removes free-text and location fields.

```bash
# input stays local; output is the file that is safe to share / deploy
python make_redacted_data.py data/real/<raw_pull>.csv data/real/tier1_redacted.csv
```

Run this on every new data pull. Keep the raw pull off any shared system.

## Project layout

```
app.py                     # entry point, page layout, tab wiring
make_redacted_data.py      # produces the PII-safe assessment file
requirements.txt
src/
  data_loader.py           # loads + filters assessments and survey data
  geography_loader.py      # facility -> sub-county crosswalk, assessment counts
  render_geography.py      # the deployment-reach choropleth
  plot_theme.py            # shared colour palette and Plotly template
  styles.py                # injected CSS (canvas, typography, cards)
  tabs/                    # one module per dashboard view
data/
  real/                    # data files go here (git-ignored, ships empty)
```

## Notes

- The dashboard is descriptive (counts, distributions, at-a-glance views) and is
  not a substitute for the formal analysis.
