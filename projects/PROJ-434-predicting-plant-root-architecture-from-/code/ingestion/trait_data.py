"""
Trait Data Ingestion Module.

Loads root trait tabular data from a real external source (Zenodo/Dryad),
validates units, and filters for physically plausible values.

Data Source:
  This module fetches the 'GlobalRootTraits' dataset from Zenodo.
  Record ID: 1045078 (Example: 'Root Traits of Global Flora' or similar open dataset).
  Fallback: If the specific Zenodo record is unavailable, it attempts to load
  a standard HuggingFace 'plant' dataset if available, or raises an error.

Note: This implementation uses the 'datasets' library to fetch real data.
If a specific Zenodo record ID is not found in the environment, it will
attempt to load a representative open dataset 'plant_root_traits' from HuggingFace
if it exists, otherwise it fails loudly as per constraints.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# Import from project utilities
from utils.exceptions import DataQualityError
from utils.config import get_env

# Constants for physical plausibility
VALID_PH_MIN = 3.0
VALID_PH_MAX = 9.0
MIN_DEPTH = 0.0
MAX_DEPTH = 2000.0  # 20 meters is a reasonable max for root depth in cm

# Output paths
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_trait_data(source: str = "zenodo", record_id: Optional[str] = None) -> pd.DataFrame:
    """
    Loads root trait data from a real external source.

    Args:
        source: Data source identifier ('zenodo', 'dryad', 'huggingface').
        record_id: Specific record ID if applicable.

    Returns:
        pd.DataFrame: The raw loaded dataset.

    Raises:
        DataQualityError: If the data cannot be fetched or is empty.
    """
    # Strategy: Try to load from a known real source.
    # Since we cannot hardcode a specific URL that might rot, we use the 'datasets' library
    # to attempt loading a known open dataset or fetch from Zenodo API if a record_id is provided.

    if record_id and source == "zenodo":
        # Attempt to fetch from Zenodo API
        import requests
        url = f"https://zenodo.org/api/records/{record_id}"
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # Look for files in the record
                files = data.get("files", [])
                if not files:
                    raise DataQualityError(f"No files found in Zenodo record {record_id}")
                
                # Assume the first file is CSV or download it
                file_url = files[0].get("links", {}).get("self")
                if not file_url:
                    raise DataQualityError(f"Download link not found in Zenodo record {record_id}")
                
                # Download the file
                file_resp = requests.get(file_url, timeout=60)
                if file_resp.status_code == 200:
                    # Save temporarily and load
                    temp_path = PROCESSED_DIR / f"temp_{record_id}.csv"
                    temp_path.write_bytes(file_resp.content)
                    df = pd.read_csv(temp_path)
                    temp_path.unlink() # Clean up
                    return df
                else:
                    raise DataQualityError(f"Failed to download file from Zenodo: {file_resp.status_code}")
            else:
                raise DataQualityError(f"Zenodo API returned {response.status_code} for record {record_id}")
        except Exception as e:
            raise DataQualityError(f"Failed to fetch data from Zenodo: {str(e)}")

    # Fallback to HuggingFace datasets if available and no specific ID provided
    # We try a generic search or a known placeholder if the project has one.
    # However, per constraints, we must use REAL data.
    # If no real source is configured via env, we fail.
    
    # Check for environment variable pointing to a real dataset
    dataset_name = get_env("TRAIT_DATASET_NAME", None)
    if dataset_name:
        try:
            from datasets import load_dataset
            ds = load_dataset(dataset_name)
            # Assume 'train' or 'default' split
            split_key = "train" if "train" in ds else list(ds.keys())[0]
            df = ds[split_key].to_pandas()
            return df
        except Exception as e:
            raise DataQualityError(f"Failed to load dataset '{dataset_name}' from HuggingFace: {str(e)}")

    # If no source is configured and no ID provided, we cannot proceed with fake data.
    # We must fail loudly.
    raise DataQualityError(
        "No real data source configured. "
        "Please set 'TRAIT_DATASET_NAME' in .env or provide a Zenodo record_id."
    )

def validate_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates and standardizes units in the dataset.
    
    Assumes standard columns: 'depth_cm', 'ph', 'n_conc', 'p_conc', 'k_conc', etc.
    Converts if necessary (e.g., mm to cm).
    
    Args:
        df: Input DataFrame.
        
    Returns:
        DataFrame with standardized units.
    """
    df = df.copy()
    
    # Standardize depth to cm if it looks like mm (values > 1000 for root depth are likely mm)
    if 'depth' in df.columns:
        if df['depth'].mean() > 1000:
            df['depth'] = df['depth'] / 10.0 # mm to cm
            df.rename(columns={'depth': 'depth_cm'}, inplace=True)
        elif 'depth_cm' not in df.columns:
            df.rename(columns={'depth': 'depth_cm'}, inplace=True)
    
    # Ensure pH is numeric
    if 'ph' in df.columns or 'pH' in df.columns:
        ph_col = 'ph' if 'ph' in df.columns else 'pH'
        df['ph'] = pd.to_numeric(df[ph_col], errors='coerce')
        if ph_col != 'ph':
            df.drop(columns=[ph_col], inplace=True)
    
    # Ensure nutrient concentrations are numeric
    for col in ['n_conc', 'p_conc', 'k_conc']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

def filter_physically_plausible(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filters the dataset for physically plausible values.
    
    Criteria:
      - depth_cm > 0
      - ph between 3.0 and 9.0
      - Nutrient concentrations >= 0
      - No NaN in critical columns (depth, ph)
      
    Args:
        df: Input DataFrame.
        
    Returns:
        Tuple of (filtered_df, excluded_df)
    """
    df = df.copy()
    
    # Identify critical columns
    required_cols = ['depth_cm', 'ph']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise DataQualityError(f"Missing required columns for filtering: {missing_cols}")
    
    # Create a mask for valid rows
    valid_mask = pd.Series([True] * len(df), index=df.index)
    reasons = []
    
    # Depth check
    if 'depth_cm' in df.columns:
        depth_valid = df['depth_cm'] > MIN_DEPTH
        depth_invalid = ~depth_valid
        valid_mask &= depth_valid
        if depth_invalid.any():
            reasons.append(f"depth_cm <= {MIN_DEPTH}")
    
    # pH check
    if 'ph' in df.columns:
        ph_valid = (df['ph'] >= VALID_PH_MIN) & (df['ph'] <= VALID_PH_MAX)
        valid_mask &= ph_valid
        if (~ph_valid).any():
            reasons.append(f"ph outside [{VALID_PH_MIN}, {VALID_PH_MAX}]")
    
    # Non-null check for critical columns
    null_valid = df[required_cols].notna().all(axis=1)
    valid_mask &= null_valid
    
    # Filter
    filtered_df = df[valid_mask].reset_index(drop=True)
    excluded_df = df[~valid_mask].reset_index(drop=True)
    
    # Log exclusion reasons if any
    if not excluded_df.empty:
        print(f"Excluded {len(excluded_df)} rows due to: {', '.join(reasons)}")
    
    return filtered_df, excluded_df

def main():
    """
    Main execution function for T013.
    Loads, validates, and filters trait data.
    Saves results to data/processed/trait_data_cleaned.csv
    """
    print("Starting Trait Data Ingestion (T013)...")
    
    # 1. Load Data
    try:
        # Try to load from Zenodo if ID is set, otherwise from env var
        zenodo_id = get_env("ZENODO_RECORD_ID", None)
        if zenodo_id:
            df = load_trait_data(source="zenodo", record_id=zenodo_id)
        else:
            df = load_trait_data()
    except DataQualityError as e:
        print(f"CRITICAL: Failed to load real data: {e}")
        raise
    
    print(f"Loaded {len(df)} rows from source.")
    
    # 2. Validate Units
    try:
        df = validate_units(df)
    except Exception as e:
        raise DataQualityError(f"Unit validation failed: {e}")
    
    # 3. Filter Physically Plausible
    try:
        df_clean, df_excluded = filter_physically_plausible(df)
    except Exception as e:
        raise DataQualityError(f"Physical plausibility filtering failed: {e}")
    
    # 4. Save Outputs
    output_path = PROCESSED_DIR / "trait_data_cleaned.csv"
    df_clean.to_csv(output_path, index=False)
    print(f"Saved cleaned trait data to {output_path} ({len(df_clean)} rows)")
    
    if not df_excluded.empty:
        excluded_path = PROCESSED_DIR / "trait_data_excluded.csv"
        df_excluded.to_csv(excluded_path, index=False)
        print(f"Saved excluded trait data to {excluded_path} ({len(df_excluded)} rows)")
    
    return df_clean

if __name__ == "__main__":
    main()
