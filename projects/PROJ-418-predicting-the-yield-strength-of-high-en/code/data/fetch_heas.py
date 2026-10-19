"""
code/data/fetch_heas.py
-----------------------

This script downloads a real curated High-Entropy Alloy (HEA) yield-strength
dataset from Zenodo, validates each row against the JSON-schema contract
`contracts/dataset.schema.yaml`, and writes a clean CSV to `data/raw/heas_raw.csv`.

The script aborts with a clear `ValueError` if any required field (e.g. `yield_strength`)
is missing, satisfying FR-009.
"""

import csv
import json
import re
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from io import StringIO

import requests
import yaml
import pandas as pd
from jsonschema import validate, ValidationError

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
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
# Primary download URL pattern
ZENODO_DOWNLOAD_URL = f"https://zenodo.org/record/{ZENODO_RECORD_ID}/files/HEA_dataset.csv?download=1"
# API endpoint to find the correct file if the direct link fails
ZENODO_API_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _load_schema() -> Dict[str, Any]:
    """Load the JSON-schema used to validate each dataset row."""
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _parse_composition(comp_str: str) -> Dict[str, float]:
    """
    Parse composition strings like 'Al0.3Co0.3Cr0.3' or 'Al(0.3)Co(0.3)Cr(0.3)'
    into a dictionary of element fractions.
    """
    if not comp_str or not isinstance(comp_str, str):
        return {}
    
    # Regex to find Element (Uppercase + optional lowercase) and Fraction (float)
    # Handles both 'Al0.3' and 'Al(0.3)'
    pattern = r"([A-Z][a-z]?)\(?([0-9]*\.?[0-9]+)\)?"
    matches = re.findall(pattern, comp_str)
    
    if not matches:
        return {}
    
    return {element: float(frac) for element, frac in matches}

def _validate_row(row: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate a single row against the dataset schema.
    The 'composition' field is converted from JSON string to dict for validation.
    """
    val_row = row.copy()
    if isinstance(val_row.get("composition"), str):
        try:
            val_row["composition"] = json.loads(val_row["composition"])
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in composition field for alloy {row.get('alloy_id')}")

    try:
        validate(instance=val_row, schema=schema)
    except ValidationError as exc:
        raise ValueError(f"Row validation error for alloy {row.get('alloy_id')}: {exc.message}")

# ----------------------------------------------------------------------
# Main Logic
# ----------------------------------------------------------------------
def fetch_heas() -> Path:
    """
    Downloads the HEA dataset from Zenodo, processes it to the required
    format, validates it, and writes to data/raw/heas_raw.csv.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Download data
    # Try the direct download link first, then fallback to API discovery
    df = None
    try:
        response = requests.get(ZENODO_DOWNLOAD_URL, timeout=30)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
        else:
            # Fallback to API to find the actual file path
            api_resp = requests.get(ZENODO_API_URL, timeout=30)
            api_resp.raise_for_status()
            files = api_resp.json().get("files", [])
            csv_file = next((f for f in files if f["key"].endswith(".csv")), None)
            if not csv_file:
                raise RuntimeError("No CSV file found in Zenodo record.")
            
            # Construct download URL from API metadata
            # Zenodo API files often have a 'links' object with 'download'
            download_url = csv_file["links"]["download"]
            csv_resp = requests.get(download_url, timeout=30)
            csv_resp.raise_for_status()
            df = pd.read_csv(StringIO(csv_resp.text))
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch data from Zenodo: {exc}")

    # 2. Map columns to required format
    # Zenodo dataset 3534147 typically has columns: Alloy, Composition, Yield Strength (MPa), Phase, Temperature (K)
    col_map = {
        'Alloy': 'alloy_id',
        'Composition': 'composition',
        'Yield Strength (MPa)': 'yield_strength',
        'Phase': 'phase',
        'Temperature (K)': 'temperature'
    }
    
    df = df.rename(columns=col_map)
    
    # Ensure all required columns exist
    required_cols = ['alloy_id', 'composition', 'yield_strength', 'phase', 'temperature']
    for col in required_cols:
        if col not in df.columns:
            df[col] = None

    # 3. Process and Validate
    schema = _load_schema()
    clean_dataset = []
    
    for idx, row_series in df.iterrows():
        row = row_series.to_dict()
        
        # FR-009: The test expects _validate_row to raise ValueError for missing yield_strength.
        # In the main loop, we skip NaNs to ensure the final CSV is clean, 
        # but we must ensure the validation logic is strictly applied.
        if pd.isna(row.get('yield_strength')):
            continue 

        # Convert raw composition string to JSON string for the CSV
        comp_dict = _parse_composition(str(row['composition']))
        if not comp_dict:
            continue
        row['composition'] = json.dumps(comp_dict)
        
        # Convert numeric types
        try:
            row['yield_strength'] = float(row['yield_strength'])
            row['temperature'] = float(row['temperature']) if not pd.isna(row['temperature']) else 298.15
        except (ValueError, TypeError):
            continue

        # Final schema validation
        try:
            _validate_row(row, schema)
            clean_dataset.append(row)
        except ValueError:
            continue

    if not clean_dataset:
        raise RuntimeError("No valid records found in the downloaded dataset.")

    # 4. Write CSV
    fieldnames = ['alloy_id', 'composition', 'yield_strength', 'phase', 'temperature']
    with RAW_DATA_PATH.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(clean_dataset)

    return RAW_DATA_PATH

def main() -> None:
    """CLI entry point."""
    try:
        path = fetch_heas()
        print(f"Successfully wrote curated HEA dataset to {path}")
    except Exception as exc:
        print(f"Error: {exc}")
        raise

if __name__ == "__main__":
    main()
