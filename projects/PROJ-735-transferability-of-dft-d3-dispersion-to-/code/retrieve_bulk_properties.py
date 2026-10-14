"""Retrieve experimental bulk-property data (FR-008, task T024).

Strategy (per spec FR-008):
  1. Attempt the NIST IL Thermophysical Database API. The spec's
     endpoint placeholder is empty, so the attempt is made against a
     configurable URL and, when it is unavailable or returns
     incomplete data, we fall back to the static CSV shipped with the
     benchmark set: ``data/experimental_bulk_properties.csv``.
  2. Verify required columns (``pair_id``, ``density``, ``viscosity``)
     and validate every record against
     ``contracts/raw_bulk_properties.schema.yaml``.
  3. Write the cleaned table to ``data/processed/bulk_properties.csv``.

The loader fails loudly: if neither the API nor the static fallback
file yields usable data, an exception is raised (no synthetic data).
"""

import json
import sys
from pathlib import Path

import pandas as pd
import requests
import yaml
from jsonschema import validate

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

NIST_API_URL = ""  # spec endpoint placeholder is empty
REQUEST_TIMEOUT_S = 15

FALLBACK_CSV = paths.data("raw", "experimental_bulk_properties.csv")
OUTPUT_CSV = paths.data("processed", "bulk_properties.csv")
SCHEMA_PATH = paths.root / "contracts" / "raw_bulk_properties.schema.yaml"

REQUIRED_COLUMNS = ["pair_id", "density", "viscosity"]


def fetch_from_nist_api(url):
    """Attempt to fetch bulk properties from the NIST API.

    Returns a DataFrame on success or None when the API is not
    reachable / does not return usable records. The spec leaves the
    endpoint empty, so in practice this returns None and the static
    fallback is used (the fallback is the documented data source).
    """
    if not url:
        log.info("NIST API endpoint not configured; using static fallback.")
        return None
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT_S)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.warning("NIST API request failed: %s", exc)
        return None
    try:
        payload = resp.json()
    except ValueError:
        log.warning("NIST API returned non-JSON payload.")
        return None
    records = payload if isinstance(payload, list) else payload.get("data")
    if not records:
        log.warning("NIST API returned no records.")
        return None
    df = pd.DataFrame(records)
    if "pair_id" not in df.columns:
        log.warning("NIST API payload lacks 'pair_id'; data incomplete.")
        return None
    return df


def normalize_columns(df):
    """Standardize column names to the contract vocabulary."""
    rename = {
        "density_g_cm3": "density",
        "density_g_cm_3": "density",
        "viscosity_cP": "viscosity",
        "viscosity_cp": "viscosity",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    return df


def load_static_fallback(path):
    """Load the static CSV shipped with the benchmark set."""
    if not path.is_file():
        raise FileNotFoundError(
          "Static bulk-property fallback not found: %s" % path
        )
    df = pd.read_csv(path)
    log.info("Loaded %d rows from static fallback %s", len(df), path)
    return df


def clean(df):
    """Validate required columns, drop rows with missing values or
    duplicate pair_ids, and coerce numeric columns."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
          "Bulk-property data is missing required columns: %s" % missing
        )
    df = df[REQUIRED_COLUMNS].copy()
    df["pair_id"] = df["pair_id"].astype(str).str.strip()
    for col in ("density", "viscosity"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    before = len(df)
    df = df.dropna(subset=REQUIRED_COLUMNS)
    dropped_na = before - len(df)
    df = df.drop_duplicates(subset=["pair_id"], keep="first")
    dropped_dup = before - dropped_na - len(df)
    if dropped_na:
        log.warning("Omitted %d rows with missing values.", dropped_na)
    if dropped_dup:
        log.warning("Omitted %d duplicate pair_id rows.", dropped_dup)
    if df.empty:
        raise ValueError("No valid bulk-property records remain after cleaning.")
    return df.reset_index(drop=True)


def validate_schema(df):
    """Validate the records against contracts/raw_bulk_properties.schema.yaml."""
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError("Schema file not found: %s" % SCHEMA_PATH)
    with open(SCHEMA_PATH, "r") as fh:
        schema = yaml.safe_load(fh)
    records = json.loads(df.to_json(orient="records"))
    validate(instance=records, schema=schema)
    log.info("Validated %d records against %s", len(records), SCHEMA_PATH)


def main():
    df = fetch_from_nist_api(NIST_API_URL)
    source = "nist_api"
    if df is None:
        df = load_static_fallback(FALLBACK_CSV)
        source = "static_fallback"
    df = normalize_columns(df)
    df = clean(df)
    validate_schema(df)
    df.to_csv(OUTPUT_CSV, index=False)
    log.info(
        "Wrote %d bulk-property records (source=%s) to %s",
        len(df), source, OUTPUT_CSV,
    )
    return df


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error("Bulk-property retrieval failed: %s", exc)
        sys.exit(1)
