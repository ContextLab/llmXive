"""
code/data/fetch_heas.py
-----------------------

This script downloads a real curated High‑Entropy Alloy (HEA) yield‑strength
dataset from Zenodo, validates each row against the JSON‑schema contract
`contracts/dataset.schema.yaml`, and writes a clean CSV to
`data/raw/heas_raw.csv`.

The script aborts with a clear `ValueError` if any required field (e.g.
`yield_strength`) is missing, satisfying FR‑009.
"""

import csv
import json
import re
import io
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import requests
import yaml
from jsonschema import ValidationError, validate

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]          # <project_root>
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DATA_PATH = RAW_DATA_DIR / "heas_raw.csv"

CONTRACTS_DIR = (
    PROJECT_ROOT
    / "specs"
    / "001-predicting-the-yield-strength-of-high-en"
    / "contracts"
)
SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"

# Zenodo Record ID for the curated HEA dataset
ZENODO_RECORD_ID = "3534147"
# Primary direct download URL (CSV)
ZENODO_DOWNLOAD_URL = f"https://zenodo.org/record/{ZENODO_RECORD_ID}/files/HEA_dataset.csv?download=1"
# Zenodo API endpoint (fallback)
ZENODO_API_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_schema() -> Dict[str, Any]:
    """Load the JSON‑schema used to validate each dataset row."""
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _parse_composition(comp_str: str) -> Dict[str, float]:
    """
    Parse composition strings like ``Al0.3Co0.3Cr0.3`` or
    ``Al(0.3)Co(0.3)Cr(0.3)`` into a dictionary of element fractions.
    """
    if not comp_str or not isinstance(comp_str, str):
        return {}

    # Regex matches an element symbol followed by a number (optionally in parentheses)
    pattern = r"([A-Z][a-z]?)\\(?([0-9]*\\.?[0-9]+)\\)?"
    matches = re.findall(pattern, comp_str)
    if not matches:
        return {}

    return {element: float(frac) for element, frac in matches}

def _validate_row(row: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate a single row against the dataset schema.
    The ``composition`` field is converted from a JSON string to ``dict`` for validation.
    """
    val_row = row.copy()
    if isinstance(val_row.get("composition"), str):
        try:
            val_row["composition"] = json.loads(val_row["composition"])
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON in composition field for alloy {row.get('alloy_id')}: {exc}"
            ) from exc

    try:
        validate(instance=val_row, schema=schema)
    except ValidationError as exc:
        raise ValueError(
            f"Row validation error for alloy {row.get('alloy_id')}: {exc.message}"
        ) from exc

def _standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename columns to the required canonical names.
    Handles a variety of possible column headings that may appear in the
    Zenodo CSV. Matching is case‑insensitive and ignores whitespace.
    """
    # Normalise column names: lower‑case, strip spaces
    df = df.rename(columns=lambda col: col.strip().lower())

    # Mapping from possible source names to required names
    col_map = {
        # alloy identifier
        "alloy": "alloy_id",
        "alloy_id": "alloy_id",
        "sample": "alloy_id",
        # composition
        "composition": "composition",
        "comp": "composition",
        "formula": "composition",
        # yield strength
        "yield_strength": "yield_strength",
        "yieldstrength": "yield_strength",
        "yield strength": "yield_strength",
        "yield_strength (mpa)": "yield_strength",
        "yield strength (mpa)": "yield_strength",
        "ys": "yield_strength",
        # phase
        "phase": "phase",
        "phase_type": "phase",
        # temperature
        "temperature": "temperature",
        "temp": "temperature",
        "temperature (k)": "temperature",
        "temp (k)": "temperature",
    }

    rename_dict = {}
    for col in df.columns:
        std_name = col_map.get(col)
        if std_name:
            rename_dict[col] = std_name

    df = df.rename(columns=rename_dict)

    # Ensure all required columns exist; if missing, create with NaN
    required = ["alloy_id", "composition", "yield_strength", "phase", "temperature"]
    for req in required:
        if req not in df.columns:
            df[req] = pd.NA

    return df

# ----------------------------------------------------------------------
# Main logic
# ----------------------------------------------------------------------
def fetch_heas() -> Path:
    """
    Downloads the HEA dataset from Zenodo, processes it to the required
    format, validates each row, and writes the cleaned CSV to
    ``data/raw/heas_raw.csv``.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------
    # 1. Download the CSV
    # --------------------------------------------------------------
    try:
        resp = requests.get(ZENODO_DOWNLOAD_URL, timeout=30)
        if resp.status_code == 200:
            df = pd.read_csv(io.StringIO(resp.text))
        else:
            # Fallback to API lookup if direct URL fails
            api_resp = requests.get(ZENODO_API_URL, timeout=30)
            api_resp.raise_for_status()
            files = api_resp.json().get("files", [])
            csv_meta = next((f for f in files if f["key"].lower().endswith(".csv")), None)
            if not csv_meta:
                raise RuntimeError("No CSV file found in Zenodo record.")
            download_url = csv_meta["links"]["download"]
            csv_resp = requests.get(download_url, timeout=30)
            csv_resp.raise_for_status()
            df = pd.read_csv(io.StringIO(csv_resp.text))
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch HEA dataset from Zenodo: {exc}") from exc

    # --------------------------------------------------------------
    # 2. Standardise column names
    # --------------------------------------------------------------
    df = _standardise_columns(df)

    # --------------------------------------------------------------
    # 3. Row‑wise processing & validation
    # --------------------------------------------------------------
    schema = _load_schema()
    clean_rows: List[Dict[str, Any]] = []

    for _, row_series in df.iterrows():
        row = row_series.to_dict()

        # Skip rows without a numeric yield strength (FR‑009)
        if pd.isna(row.get("yield_strength")):
            continue

        # Parse composition string into a JSON‑compatible dict
        comp_dict = _parse_composition(str(row.get("composition", "")))
        if not comp_dict:
            continue  # unable to parse composition → discard

        row["composition"] = json.dumps(comp_dict)

        # Convert numeric fields; provide sensible defaults where possible
        try:
            row["yield_strength"] = float(row["yield_strength"])
        except (TypeError, ValueError):
            continue

        # Temperature: if missing, assume room temperature (298.15 K)
        try:
            if pd.isna(row.get("temperature")):
                row["temperature"] = 298.15
            else:
                row["temperature"] = float(row["temperature"])
        except (TypeError, ValueError):
            row["temperature"] = 298.15

        # Validate against the JSON schema; any validation error discards the row
        try:
            _validate_row(row, schema)
        except ValueError:
            continue

        clean_rows.append(row)

    if not clean_rows:
        raise RuntimeError("No valid records were found after processing the dataset.")

    # --------------------------------------------------------------
    # 4. Write the cleaned CSV
    # --------------------------------------------------------------
    fieldnames = ["alloy_id", "composition", "yield_strength", "phase", "temperature"]
    with RAW_DATA_PATH.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(clean_rows)

    return RAW_DATA_PATH

def main() -> None:
    """CLI entry point."""
    try:
        out_path = fetch_heas()
        print(f"Successfully wrote curated HEA dataset to {out_path}")
    except Exception as exc:
        print(f"Error: {exc}")
        raise

if __name__ == "__main__":
    main()