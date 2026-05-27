"""
make_redacted_data.py

Produce a PII-safe copy of a Tier 1 assessment pull for sharing / deployment.

Usage:
    python make_redacted_data.py [input_csv] [output_csv]
    # defaults: data/real/tier1_full_fresh.csv  ->  data/real/tier1_redacted.csv

What it does (deterministic, repeatable for every future pull):
  - Keeps ONLY the columns the dashboard actually uses.
  - Replaces the free-text `symptoms` field with `symptoms_len` (character count),
    so no raw symptom text (which may contain names) ever leaves the machine.
  - Drops everything else (GPS, vitals, free-text clinical notes, referral text,
    hardware detail, etc.) since the dashboard does not use them.

The raw input stays on your machine. Share ONLY the output file.
"""

import sys
import pandas as pd

# The columns the dashboard reads. `symptoms` is handled specially (length only).
KEEP_COLS = [
    "id",                   # used for junk-prefix filtering
    "device_token",         # distinct-devices count (kept as-is per decision)
    "submitted_at",         # timestamp (upload time)
    "client_timestamp_ms",  # true assessment time -> pilot-window filter + daily volume
    "role",                 # condition-by-role heatmap
    "triage_level",         # referral chart + confidence-by-urgency
    "condition",            # top conditions (diagnostic labels, not personal data)
    "confidence",           # confidence-by-urgency
    "guidance_used",        # guidance donut
    "device_model",         # inference-by-device
    "ner_flagged",          # privacy safety-net
    "inference_ms",         # inference distribution + complexity scatter
]


def redact(input_csv, output_csv):
    df = pd.read_csv(input_csv, dtype=str)

    # 1. derive symptoms_len from the raw text, then discard the text itself
    if "symptoms" in df.columns:
        df["symptoms_len"] = df["symptoms"].fillna("").astype(str).str.len()
    else:
        df["symptoms_len"] = 0

    # 2. keep only the safe columns (those present) + symptoms_len
    cols = [c for c in KEEP_COLS if c in df.columns] + ["symptoms_len"]
    out = df[cols].copy()

    # 3. write
    out.to_csv(output_csv, index=False)

    dropped = [c for c in df.columns if c not in cols and c != "symptoms"]
    print(f"Read {len(df)} rows, {len(df.columns)} columns from {input_csv}")
    print(f"Wrote {len(out)} rows, {len(out.columns)} columns to {output_csv}")
    print(f"Kept: {', '.join(cols)}")
    print(f"Dropped {len(dropped)} unused/sensitive columns (incl. raw symptoms text, GPS, vitals, clinical notes).")


if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "data/real/tier1_full_fresh.csv"
    out = sys.argv[2] if len(sys.argv) > 2 else "data/real/tier1_redacted.csv"
    redact(inp, out)
