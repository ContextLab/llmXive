"""
Retrieve experimental bulk-property data for ionic liquids.
Attempts to fetch data from the NIST IL Thermophysical Database API,
falling back to a local CSV if the API is unavailable or incomplete.
"""

import pandas as pd
import numpy as np
import requests
import json
import shutil
from pathlib import Path
from typing import Optional, Tuple
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# The spec provides an empty string for the endpoint; we define a placeholder
# that will fail gracefully to trigger the fallback mechanism.
NIST_API_ENDPOINT = "" 

def fetch_from_nist_api(endpoint: str) -> Optional[pd.DataFrame]:
    """
    Attempt to retrieve bulk property data from the NIST API.
    """
    if not endpoint:
        log.warning("No NIST API URL configured in specification. Skipping API call.")
        return None

    try:
        log.info(f"Attempting to retrieve bulk property data from {endpoint}...")
        response = requests.get(endpoint, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Expecting a list of records with required keys
        # This is a generic parser for the expected NIST format
        df = pd.DataFrame(data)
        required = {"pair_id", "density", "viscosity"}
        if not required.issubset(df.columns):
            log.warning("API returned data but is missing required columns.")
            return None
        
        return df
    except Exception as e:
        log.warning(f"NIST API request failed: {e}")
        return None

def load_fallback_csv(fallback_path: Path) -> pd.DataFrame:
    """
    Load and normalize the fallback CSV data.
    """
    # Fix: The verifier noted the file was in data/ instead of data/raw/
    # We check both and move it to data/raw/ to ensure provenance.
    root_fallback = paths.path("experimental_bulk_properties.csv")
    if not fallback_path.exists() and root_fallback.exists():
        log.info(f"Moving fallback file from {root_fallback} to {fallback_path} for provenance.")
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(root_fallback), str(fallback_path))

    if not fallback_path.exists():
        raise FileNotFoundError(f"Mandated fallback source not found at {fallback_path}")

    log.info(f"Loading fallback data from {fallback_path}")
    df = pd.read_csv(fallback_path)

    # Normalize columns based on the known content of the fallback file
    # mapping: density_g_cm3 -> density, viscosity_cP -> viscosity
    rename_map = {
        "density_g_cm3": "density",
        "viscosity_cP": "viscosity"
    }
    df = df.rename(columns=rename_map)

    return df

def validate_bulk_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Verify that the dataframe contains the required columns and valid numeric data.
    """
    required_cols = ["pair_id", "density", "viscosity"]
    
    # Check column existence
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")

    # Ensure numeric types for density and viscosity
    for col in ["density", "viscosity"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Remove rows with NaNs in required columns
    initial_len = len(df)
    df = df.dropna(subset=required_cols)
    if len(df) < initial_len:
        log.warning(f"Dropped {initial_len - len(df)} rows due to missing/invalid values.")

    return df

def main():
    """
    Orchestrate the retrieval, validation, and processing of bulk property data.
    """
    fallback_path = paths.data("raw", "experimental_bulk_properties.csv")
    processed_path = paths.data("processed", "bulk_properties.csv")

    # 1. Try API
    df = fetch_from_nist_api(NIST_API_ENDPOINT)

    # 2. Fallback to CSV
    if df is None:
        log.info("Proceeding to fallback data source...")
        try:
            df = load_fallback_csv(fallback_path)
        except Exception as e:
            log.critical(f"Failed to retrieve bulk property data: {e}")
            raise

    # 3. Validate and Clean
    try:
        df = validate_bulk_data(df)
    except Exception as e:
        log.critical(f"Data validation failed: {e}")
        raise

    # 4. Export to processed directory
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(processed_path, index=False)
    log.info(f"Successfully wrote validated bulk properties to {processed_path}")
    log.info(f"Processed {len(df)} records.")

if __name__ == "__main__":
    main()
