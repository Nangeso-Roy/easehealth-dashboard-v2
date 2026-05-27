"""
Data loaders for the Ease Health pilot dashboard.

Reads from three sources:
  1. PostgreSQL exports (CSV) — real app data, in data/real/
  2. Field log (CSV) — real, cleaned from Google Form, in data/real/
  3. Kobo CRF (CSV) — synthetic for now, in data/synthetic/
     (Will switch to data/real/ when actual Kobo exports start arriving.)

The dashboard only ever calls these functions; it never knows or cares where
the data physically comes from.
"""

import ast
from functools import lru_cache
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_REAL = PROJECT_ROOT / "data" / "real"
DATA_SYNTHETIC = PROJECT_ROOT / "data" / "synthetic"

PILOT_START = pd.Timestamp("2026-04-27", tz="UTC")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_pg_array(value):
    """
    PostgreSQL exports text arrays as strings like '{"item1","item2"}'.
    Convert to a Python list. Empty arrays and NaN return [].
    """
    if pd.isna(value) or value in ("", "{}"):
        return []
    s = str(value).strip()
    if not (s.startswith("{") and s.endswith("}")):
        return []
    inner = s[1:-1]
    if not inner:
        return []
    # Quoted items — handle commas inside quoted strings
    try:
        # Wrap in brackets and let ast handle escapes
        return list(ast.literal_eval("[" + inner + "]"))
    except (ValueError, SyntaxError):
        # Fallback: simple comma split, strip quotes
        return [x.strip().strip('"') for x in inner.split(",") if x.strip()]


def _to_numeric_safe(series):
    """Try to convert a series to numeric; non-numeric values become NaN."""
    return pd.to_numeric(series, errors="coerce")


def canonical_condition(raw):
    """
    Collapse the free-text `condition` field into clean, grouped labels.
    Same logic used across Snapshot and Clinical Activity so the two agree.
    Keeps the raw string elsewhere — the messy/hallucinated originals are a
    real AI-quality signal surfaced on the Safety tab, not here.
    """
    if not isinstance(raw, str) or not raw.strip():
        return None
    s = raw.strip().lower()
    if "malaria" in s:
        return "Malaria (all forms)"
    if "pneumonia" in s:
        return "Pneumonia"
    if "meningitis" in s:
        return "Meningitis"
    if "diarrh" in s:
        return "Diarrhoea"
    if "cold" in s or "urti" in s or "upper respiratory" in s or "rhinitis" in s:
        return "Common cold / URTI"
    return raw.strip().title()[:40]


# ---------------------------------------------------------------------------
# Tier 1 assessments — the rich app data
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_assessments():
    """
    Load Tier 1 assessment data, filtered to the pilot window (>= 2026-04-27).

    Returns one row per assessment with all 48 Tier 1 columns. Array columns
    (treatment, next_steps, confirmed_signs, red_flags, issue_tags,
    referral_reasons) are returned as Python lists. Numeric columns are cast.
    Timestamps are timezone-aware UTC.
    """
    path = DATA_REAL / "tier1_redacted.csv"
    df = pd.read_csv(path)

    # Timestamps
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True, errors="coerce")

    # Numeric coercions for fields that may have come through as strings
    numeric_cols = [
        "client_timestamp_ms", "latitude", "longitude", "location_accuracy_m",
        "android_api", "total_ram_mb", "max_cpu_freq_mhz", "cpu_count",
        "recommended_n_batch", "inference_ms",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = _to_numeric_safe(df[col])

    # TRUE assessment time comes from client_timestamp_ms (device clock),
    # not submitted_at (server upload time, which includes late syncs).
    client_at = pd.to_datetime(df["client_timestamp_ms"], unit="ms", utc=True)
    df["client_at"] = client_at.dt.tz_convert("Africa/Kampala")
    df["client_date"] = df["client_at"].dt.date
    df["client_hour"] = df["client_at"].dt.hour

    # Filter to the true pilot window (27 Apr – 1 May 2026, Kampala-local)
    import datetime as _dt
    _start = _dt.date(2026, 4, 27)
    _end = _dt.date(2026, 5, 1)
    df = df[(df["client_date"] >= _start) & (df["client_date"] <= _end)].copy()

    # Drop the 4 known unrateable / junk assessments (by id prefix)
    _junk_prefixes = ("341c472b", "e10581e8", "c3519381", "692c189c")
    df = df[~df["id"].astype(str).str.startswith(_junk_prefixes)].copy()

    # Boolean coercion
    if "ner_flagged" in df.columns:
        df["ner_flagged"] = df["ner_flagged"].map({"t": True, "f": False, True: True, False: False})

    # Array columns — convert from PostgreSQL text-array format to Python lists
    array_cols = ["confirmed_signs", "treatment", "next_steps",
                  "red_flags", "issue_tags", "referral_reasons"]
    for col in array_cols:
        if col in df.columns:
            df[col] = df[col].apply(_parse_pg_array)

    # Canonical (grouped) condition label — used by Snapshot and Clinical Activity
    if "condition" in df.columns:
        df["condition_canonical"] = df["condition"].apply(canonical_condition)

    # Keep submitted_date/hour available too (upload-time), but client_date is canonical
    df["submitted_date"] = df["submitted_at"].dt.tz_convert("Africa/Kampala").dt.date
    df["submitted_hour"] = df["submitted_at"].dt.tz_convert("Africa/Kampala").dt.hour
    # A grouping key for "assessments that almost certainly came from the same
    # person/device pairing." NOT a count of people — see note below. Two same-cadre
    # FHWs sharing a device collapse into one worker_session_id, which undercounts
    # real humans. Use this for grouping/comparison only, never as a worker count.
    df["worker_session_id"] = df["role"].fillna("Unknown") + "::" + df["device_token"].fillna("unknown")

    return df.reset_index(drop=True)


@lru_cache(maxsize=1)
def load_tier2_assessments():
    """
    Load Tier 2 assessments. Same shape as the Metabase view, post-redaction,
    pseudonym-keyed. Used where redacted-text display is the right call.
    """
    path = DATA_REAL / "tier2_assessments.csv"
    df = pd.read_csv(path)
    df["submitted_date"] = pd.to_datetime(df["submitted_date"], errors="coerce").dt.date
    df["promoted_at"] = pd.to_datetime(df["promoted_at"], utc=True, errors="coerce")
    df = df[pd.to_datetime(df["submitted_date"]) >= PILOT_START.tz_localize(None)].copy()

    array_cols = ["confirmed_signs", "red_flags", "issue_tags"]
    for col in array_cols:
        if col in df.columns:
            df[col] = df[col].apply(_parse_pg_array)

    if "inference_ms" in df.columns:
        df["inference_ms"] = _to_numeric_safe(df["inference_ms"])

    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_audit_log():
    """Audit events recorded by the API and ETL."""
    path = DATA_REAL / "audit_log.csv"
    df = pd.read_csv(path)
    df["at"] = pd.to_datetime(df["at"], utc=True, errors="coerce")
    df = df[df["at"] >= PILOT_START].copy()
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Device registry
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_device_registry():
    """Device registry — full history, not filtered by pilot date."""
    path = DATA_REAL / "device_registry.csv"
    df = pd.read_csv(path)
    df["first_seen"] = pd.to_datetime(df["first_seen"], utc=True, errors="coerce")
    df["last_seen"] = pd.to_datetime(df["last_seen"], utc=True, errors="coerce")
    df["revoked_at"] = pd.to_datetime(df["revoked_at"], utc=True, errors="coerce")
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Field log — real Google Form data
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_field_log():
    """
    Cleaned Google Form export of FHW session logs.

    One row per session of an FHW using the app at a facility.
    Joins to assessments via facility + role + date (and time window).
    """
    path = DATA_REAL / "field_log.csv"
    df = pd.read_csv(path)
    df["date_of_session"] = pd.to_datetime(df["date_of_session"], errors="coerce").dt.date
    df["submission_timestamp"] = pd.to_datetime(df["submission_timestamp"], errors="coerce")
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Kobo CRF responses
# ---------------------------------------------------------------------------
# Code -> human-readable label maps for categorical demographics (coded Kobo file)
_KOBO_LABELS = {
    "a02_sex": {"1": "Male", "2": "Female"},
    "a03_education": {
        "2": "Secondary (O-Level)", "3": "Secondary (A-Level)", "4": "Certificate",
        "5": "Diploma", "6": "Bachelor's Degree", "7": "Postgraduate Degree",
    },
    "a04_cadre": {
        "1": "Nursing Assistant", "2": "Enrolled Nurse", "3": "Registered Nurse",
        "4": "Enrolled Midwife", "5": "Registered Midwife", "6": "Clinical Officer",
        "7": "Medical Officer", "8": "VHT Member", "9": "CHEW", "10": "Other",
    },
    "a09_digital_skill": {
        "1": "Very poor", "2": "Poor", "3": "Average", "4": "Good", "5": "Very good",
    },
}

# Numeric columns in the coded Kobo file (Likert items, scores, subscale means)
_KOBO_NUMERIC = (
    [f"c{ i:02d}_sus{i}" for i in range(1, 11)]
    + ["sus_score"]
    + ["d01_tech_speed", "d02_tech_reliable", "d03_tech_offline", "d04_wf_integrate",
       "d05_wf_time", "d06_wf_compat", "d07_infra_device", "d08_infra_battery",
       "d09_infra_space", "d10_train_sufficient", "d11_train_troubleshoot", "feasibility_mean"]
    + ["e01_trust1", "e02_trust2", "e03_trust3", "e04_satis1", "e05_satis2", "e06_satis3",
       "e07_willing1", "e08_willing2", "e09_willing3", "e10_value1", "e11_value2",
       "e12_overall", "acceptability_mean"]
    + ["f01_mal_pre", "f01_mal_post", "f02_mal_tx_pre", "f02_mal_tx_post",
       "f03_pneu_pre", "f03_pneu_post", "f04_pneu_tx_pre", "f04_pneu_tx_post",
       "f05_tb_pre", "f05_tb_post", "f06_edu_pre", "f06_edu_post",
       "f07_ref_pre", "f07_ref_post", "f08_uncert_pre", "f08_uncert_post",
       "conf_pre_mean", "conf_post_mean", "conf_change_mean"]
    + [f"g{i:02d}_pu1" for i in []]  # placeholder, real g-cols added below
    + ["g01_pu1", "g02_pu2", "g03_pu3", "g04_peou1", "g05_peou2", "g06_peou3",
       "g07_si1", "g08_si2", "g09_si3", "g10_fc1", "g11_fc2", "g12_fc3", "g13_fc4",
       "g14_ai1", "g15_ai2", "g16_ai3", "pu_mean", "peou_mean", "si_mean", "fc_mean", "ai_mean"]
    + ["a01_age", "a05_yrs_role", "b01_days_used", "b02_consults_day"]
)


@lru_cache(maxsize=1)
def load_kobo():
    """
    Kobo CRF responses — real, coded, facility-tagged (136 rows).

    Reads the CODED file (numeric Likert values + precomputed scores).
    Adds *_label columns for categorical demographics (cadre, education, sex,
    digital skill) for human-readable charts. Includes the tagged location
    columns: facility_clean, area, area_type, health_sub_district,
    facility_level_clean.
    """
    path = DATA_REAL / "kobo_tagged.xlsx"
    df = pd.read_excel(path, dtype=str)

    for col in _KOBO_NUMERIC:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col, mapping in _KOBO_LABELS.items():
        if col in df.columns:
            df[col + "_label"] = df[col].map(mapping)

    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Cache buster — call this if you've regenerated synthetic or refreshed CSVs
# ---------------------------------------------------------------------------

def clear_cache():
    """Clear all cached data. Useful in interactive development."""
    load_assessments.cache_clear()
    load_tier2_assessments.cache_clear()
    load_audit_log.cache_clear()
    load_device_registry.cache_clear()
    load_field_log.cache_clear()
    load_kobo.cache_clear()


# ---------------------------------------------------------------------------
# Smoke test — run this file directly to verify all loaders work
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Loading all sources...\n")

    a = load_assessments()
    print(f"Tier 1 assessments: {len(a)} rows, {len(a.columns)} cols")
    print(f"  Date range: {a['submitted_date'].min()} to {a['submitted_date'].max()}")
    print(f"  Distinct (role, device) sessions: {a['worker_session_id'].nunique()}  [grouping key, not a worker count]")
    print(f"  Distinct devices: {a['device_token'].nunique()}")
    print(f"  Mean inference_ms: {a['inference_ms'].mean():.0f}")
    print()

    t2 = load_tier2_assessments()
    print(f"Tier 2 assessments: {len(t2)} rows, {len(t2.columns)} cols")
    print()

    al = load_audit_log()
    print(f"Audit log: {len(al)} rows")
    print(f"  Actions: {dict(al['action'].value_counts())}")
    print()

    dr = load_device_registry()
    print(f"Device registry: {len(dr)} rows")
    print(f"  Active (not revoked): {dr['revoked_at'].isna().sum()}")
    print()

    fl = load_field_log()
    print(f"Field log: {len(fl)} rows")
    print(f"  Cadres: {dict(fl['fhw_cadre'].value_counts())}")
    print(f"  Facilities: {fl['facility_name'].nunique()}")
    print()

    k = load_kobo()
    print(f"Kobo responses: {len(k)} rows, {len(k.columns)} cols")
    print(f"  Mean SUS: {k['SUS_score'].mean():.1f}")
    print(f"  Cadres: {dict(k['A04_cadre'].value_counts())}")