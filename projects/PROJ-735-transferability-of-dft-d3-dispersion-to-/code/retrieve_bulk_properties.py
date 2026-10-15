"""
retrieve_bulk_properties.py

Retrieve experimental bulk‑property data for ionic‑liquid ion pairs.

The script attempts to fetch the data from the NIST IL Thermophysical
Database API. If the request fails (network error, non‑200 status, or
missing required fields) the script falls back to the static CSV
`data/raw/experimental_bulk_properties.csv` or `data/experimental_bulk_properties.csv`.

The resulting DataFrame is validated against the JSON‑Schema
`contracts/raw_bulk_properties.schema.yaml` and written to
`data/processed/bulk_properties.csv` with the canonical column names
`pair_id`, `density` (g·cm⁻³) and `viscosity` (cP).
"""

import json
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
import yaml
from jsonschema import validate, ValidationError

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# The NIST API endpoint is not provided in the specification, so we 
# attempt a generic GET request if configured. Otherwise, we fall back.
NIST_API_URL = ""  # Empty string → immediate fallback

# We check both the plan-specified raw directory and the observed data root
RAW_BULK_CSV_PATHS = [
    paths.data("raw", "experimental_bulk_properties.csv"),
    paths.data("experimental_bulk_properties.csv"),
]
PROCESSED_BULK_CSV = paths.data("processed", "bulk_properties.csv")
SCHEMA_PATH = paths.path("contracts", "raw_bulk_properties.schema.yaml")

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_schema(schema_path: Path) -> dict:
    """Load the JSON‑Schema used for validation."""
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)
    return schema

def _fetch_from_nist() -> Optional[pd.DataFrame]:
    """
    Attempt to retrieve the bulk‑property data from the NIST API.
    """
    if not NIST_API_URL:
        logger.info("No NIST API URL configured – using fallback CSV.")
        return None

    try:
        response = requests.get(NIST_API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        logger.info(f"Fetched {len(df)} records from NIST API.")
        return df
    except Exception as exc:
        logger.warning(f"NIST API request failed ({exc}); falling back to CSV.")
        return None

def _load_fallback_csv() -> pd.DataFrame:
    """Load the static CSV shipped with the repository from available paths."""
    for p in RAW_BULK_CSV_PATHS:
        if p.is_file():
            logger.info(f"Loading fallback bulk-property CSV from {p}")
            return pd.read_csv(p)
    
    raise FileNotFoundError(
        f"Fallback bulk-property CSV not found at any of: {RAW_BULK_CSV_PATHS}"
    )

def _standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename columns to match the contract schema.
    The raw CSV uses `density_g_cm3` and `viscosity_cP`; the contract
    expects `density` and `viscosity`.
    """
    rename_map = {}
    if "density_g_cm3" in df.columns:
        rename_map["density_g_cm3"] = "density"
    if "viscosity_cP" in df.columns:
        rename_map["viscosity_cP"] = "viscosity"
    
    if rename_map:
        df = df.rename(columns=rename_map)
        logger.info(f"Renamed columns: {rename_map}")
    return df

def _validate_dataframe(df: pd.DataFrame, schema: dict) -> None:
    """
    Validate the DataFrame against the provided JSON‑Schema.
    The schema defines the root as an array of objects.
    """
    # Convert DataFrame to a list of dictionaries (records) to match the 'array' schema
    records = df.to_dict(orient="records")
    try:
        validate(instance=records, schema=schema)
    except ValidationError as ve:
        raise ValidationError(
            f"DataFrame failed validation against schema: {ve.message}"
        ) from ve

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    """
    Retrieve bulk‑property data, validate it, and write the processed CSV.
    """
    # 1. Load data – try the API first, then fallback.
    df_raw = _fetch_from_nist()
    if df_raw is None:
        df_raw = _load_fallback_csv()

    # 2. Standardise column names.
    df = _standardise_columns(df_raw)

    # 3. Verify required columns are present.
    required = {"pair_id", "density", "viscosity"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns after standardisation: {missing}")

    # 4. Load and apply the JSON‑Schema validation.
    schema = _load_schema(SCHEMA_PATH)
    _validate_dataframe(df, schema)

    # 5. Write the processed CSV to the declared location.
    PROCESSED_BULK_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_BULK_CSV, index=False)
    logger.info(f"Wrote processed bulk-property CSV to {PROCESSED_BULK_CSV}")

if __name__ == "__main__":
    main()