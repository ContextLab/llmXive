import os
import logging
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from config import get_config
from utils import setup_logging, retry_on_failure, DataFetchError
from api_config import QUERY_PARAMS
from data_models import PlanetCategory

# Setup logging
logger = setup_logging("download")

# Constants for classification (per T011c)
HOT_JUPITER_TEMP_THRESHOLD = 1000.0  # Kelvin
SUPER_EARTH_RADIUS_THRESHOLD = 1.6   # Earth radii

def fetch_raw_metadata() -> pd.DataFrame:
    """
    Fetches raw metadata from the NASA Exoplanet Archive.
    Returns a DataFrame with all available spectra matching the criteria.
    """
    config = get_config()
    base_url = "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/Tbl/nph-exoplanetarchive"
    
    # Construct query based on api_config
    params = QUERY_PARAMS.copy()
    params['format'] = 'json'
    params['limit'] = 10000 # High limit to ensure we get all available

    logger.info(f"API request start: {base_url}")
    
    try:
        response = requests.get(base_url, params=params, timeout=60)
        logger.info(f"response status: {response.status_code}")
        response.raise_for_status()
        
        data = response.json()
        if 'data' not in data:
            raise DataFetchError("No 'data' key in API response")
        
        df = pd.DataFrame(data['data'])
        logger.info(f"Download completion: Retrieved {len(df)} records")
        return df
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise DataFetchError(f"Failed to fetch metadata: {e}")

def process_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes raw metadata to extract relevant fields and classify planets.
    """
    # Select relevant columns, renaming to match expected schema
    # Mapping based on typical NASA Exoplanet Archive columns
    col_mapping = {
        'pl_name': 'planet_name',
        'pl_eqt': 'temperature', # Equilibrium temperature
        'pl_metl': 'metallicity',
        'pl_radj': 'radius_jup', # Radius in Jupiter radii for conversion
        'snr': 'snr',
        'res': 'resolution',
        'discfacility': 'instrument'
    }
    
    # Filter columns that exist
    existing_cols = [k for k in col_mapping.keys() if k in df.columns]
    processed_df = df[existing_cols].copy()
    processed_df.rename(columns=col_mapping, inplace=True)
    
    # Ensure numeric types
    numeric_cols = ['temperature', 'metallicity', 'snr', 'resolution']
    for col in numeric_cols:
        if col in processed_df.columns:
            processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
    
    # Convert radius to Earth radii if available (1 Rjup ~ 11.209 Re)
    if 'radius_jup' in processed_df.columns:
        processed_df['radius_earth'] = processed_df['radius_jup'] * 11.209
    else:
        # Fallback or estimation if radius_jup is missing (simplified for this task)
        processed_df['radius_earth'] = np.nan

    # Classification Logic (T011c)
    def classify_planet(row):
        temp = row.get('temperature')
        radius = row.get('radius_earth')
        
        if pd.isna(temp):
            return "Unknown"
        
        if temp > HOT_JUPITER_TEMP_THRESHOLD:
            # Check if it's a gas giant (usually large radius, but temp is the primary driver here per spec)
            return PlanetCategory.HOT_JUPITER.value
        elif temp < HOT_JUPITER_TEMP_THRESHOLD and pd.notna(radius) and radius < SUPER_EARTH_RADIUS_THRESHOLD:
            return PlanetCategory.TEMPERATE_SUPER_EARTH.value
        else:
            return "Other"

    processed_df['planet_category'] = processed_df.apply(classify_planet, axis=1)
    
    # Log citation as required
    logger.info(f"Threshold: T_eq > {HOT_JUPITER_TEMP_THRESHOLD}K (Source: Fortney et al. 2008)")
    
    # Handle wavelength range (simplified: assume single value or range string from raw data if available)
    # If not present in raw, we might need to derive from instrument or leave as placeholder if not in source
    # For this implementation, we assume 'wavelength_range' is not in raw API and we derive a generic one or use instrument metadata
    # Since the spec asks for it, we'll create a placeholder based on instrument if specific data is missing, 
    # but strictly we should only use real data. Let's assume 'wavelength_range' is not in the raw JSON for now 
    # and we will fill it with a generic "N/A" or attempt to fetch if available in a different column.
    # To satisfy the schema requirement without faking data, we will leave it as 'N/A' if not found in source,
    # or map a specific column if it exists (e.g., 'pl_wavmin', 'pl_wavmax').
    if 'pl_wavmin' in df.columns and 'pl_wavmax' in df.columns:
        processed_df['wavelength_range'] = df['pl_wavmin'].astype(str) + '-' + df['pl_wavmax'].astype(str)
    else:
        processed_df['wavelength_range'] = "N/A" # Real data fallback: if not present, it's not fabricated.
    
    # Drop intermediate columns
    if 'radius_jup' in processed_df.columns:
        processed_df.drop(columns=['radius_jup'], inplace=True)
        
    return processed_df

def save_metadata_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Saves the processed metadata to a CSV file.
    Columns: [planet_name, temperature, metallicity, snr, resolution, planet_category, instrument, wavelength_range]
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure required columns exist
    required_cols = [
        'planet_name', 'temperature', 'metallicity', 'snr', 
        'resolution', 'planet_category', 'instrument', 'wavelength_range'
    ]
    
    # Filter to only existing columns to avoid KeyError if some are missing from source
    # Note: The task requires these columns. If the source doesn't have them, 
    # we must handle it gracefully but not fabricate.
    # We will check existence and warn if missing, but proceed.
    available_cols = [c for c in required_cols if c in df.columns]
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        logger.warning(f"Missing columns in source data: {missing_cols}. Proceeding with available data.")
    
    final_df = df[available_cols].copy()
    
    # Fill NaN with a specific marker for clarity in CSV, or keep as NaN
    # For numeric columns, we keep NaN. For string, we keep NaN or fill if needed.
    # The spec doesn't specify filling, so we leave as NaN.
    
    final_df.to_csv(path, index=False)
    logger.info(f"Metadata saved to {path}")

def count_unique_planets(csv_path: str) -> int:
    """
    Counts unique planets from the saved metadata CSV.
    """
    df = pd.read_csv(csv_path)
    return df['planet_name'].nunique()

def report_sample_size(count: int, output_path: str) -> None:
    """
    Reports the sample size to a JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "count": count,
        "note": "Sample size reported for informational purposes only; pipeline proceeds regardless of count."
    }
    
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Sample size report saved to {path}")

def main():
    """
    Main entry point for the download and metadata processing pipeline.
    """
    config = get_config()
    raw_output_dir = config.get('raw_data_dir', 'data/raw')
    processed_output_dir = config.get('processed_data_dir', 'data/processed')
    
    # Ensure directories exist
    Path(raw_output_dir).mkdir(parents=True, exist_ok=True)
    Path(processed_output_dir).mkdir(parents=True, exist_ok=True)
    
    # 1. Fetch
    logger.info("Starting data fetch...")
    try:
        raw_df = fetch_raw_metadata()
    except DataFetchError as e:
        logger.critical(f"Data fetch failed: {e}")
        raise
    
    # 2. Process
    logger.info("Processing metadata...")
    processed_df = process_metadata(raw_df)
    
    # 3. Save
    metadata_path = os.path.join(processed_output_dir, 'metadata.csv')
    save_metadata_csv(processed_df, metadata_path)
    
    # 4. Count & Report
    count = count_unique_planets(metadata_path)
    report_path = os.path.join(processed_output_dir, 'sample_size_report.json')
    report_sample_size(count, report_path)
    
    # 5. Count Report (T013a)
    count_report_path = os.path.join(processed_output_dir, 'count_report.json')
    with open(count_report_path, 'w') as f:
        json.dump({"count": count}, f, indent=2)
    logger.info(f"Count report saved to {count_report_path}")

if __name__ == "__main__":
    main()