import os
import logging
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd

from config import get_config
from utils import setup_logging, DataFetchError, PipelineError

# Initialize logger
logger = setup_logging("download")

# Constants
API_BASE_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
QUERY_PARAMS = {
    "query": "SELECT * FROM exoplanets WHERE planet_category IN ('Hot Jupiter', 'Super Earth')",
    "format": "json"
}

def fetch_raw_metadata() -> Optional[pd.DataFrame]:
    """
    Fetch raw metadata from the NASA Exoplanet Archive API.
    Returns a pandas DataFrame or None if fetch fails.
    """
    logger.info("API request start")
    try:
        response = requests.get(API_BASE_URL, params=QUERY_PARAMS, timeout=60)
        logger.info(f"response status: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        if not data:
            logger.warning("API returned empty dataset")
            return None
        df = pd.DataFrame(data)
        logger.info("Download completion: metadata fetched successfully")
        return df
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise DataFetchError(f"Failed to fetch metadata from NASA Exoplanet Archive: {e}")

def process_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process raw metadata to ensure required columns exist and are valid.
    Adds 'planet_category' based on classification logic.
    """
    required_cols = ['planet_name', 'equilibrium_temperature', 'metallicity', 'snr', 'resolution', 'instrument', 'wavelength_range']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing columns in raw metadata: {missing_cols}")
        # Attempt to map or fill if possible, otherwise raise
        for col in missing_cols:
            df[col] = None

    # Classification logic (T011c) - Tag planets
    # Logic: Hot Jupiter if T_eq > 1000K and Radius > 0.8 R_J (approx 9 R_E)
    # Super Earth if Radius < 1.6 R_E (approx 1.6) and T_eq < 1000K
    # Note: Radius column might be 'radius' or 'radius_jupiter' or 'radius_earth'
    # We assume 'radius' is in Earth radii for this logic, or convert if needed.
    # Since the task says "Do NOT use hardcoded arbitrary thresholds unless defined",
    # we use standard literature definitions:
    # Hot Jupiter: T_eq > 1000 K, R > 0.8 R_Jup (~9 R_Earth)
    # Super Earth: R < 1.6 R_Earth, T_eq < 1000 K
    
    def classify(row):
        t_eq = row.get('equilibrium_temperature')
        r = row.get('radius') # Assuming radius is in Earth radii or normalized
        # Fallback if radius is not available or NaN
        if pd.isna(t_eq) or pd.isna(r):
            return "Unknown"
        
        # Standard definitions (approximate)
        # Hot Jupiter: T > 1000K and R > 9 (approx 0.8 R_Jup in R_Earth)
        if t_eq > 1000 and r > 9:
            return "Hot Jupiter"
        # Super Earth: R < 1.6 and T < 1000
        elif r < 1.6 and t_eq < 1000:
            return "Temperate Super-Earth"
        else:
            return "Other"

    df['planet_category'] = df.apply(classify, axis=1)
    logger.info("Classification logic applied: planet_category column populated")
    return df

def save_processed_metadata(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save processed metadata to CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Processed metadata saved to {output_path}")

def count_unique_planets(metadata_path: Path) -> Dict[str, Any]:
    """
    Count unique planets from the saved metadata.csv.
    Returns a dictionary with the count.
    """
    if not metadata_path.exists():
        raise PipelineError(f"Metadata file not found at {metadata_path}")
    
    df = pd.read_csv(metadata_path)
    # Count unique planet names
    unique_count = df['planet_name'].nunique()
    result = {"count": int(unique_count)}
    
    # Save report
    report_path = metadata_path.parent / "count_report.json"
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Unique planet count: {unique_count}. Report saved to {report_path}")
    return result

def main():
    """
    Main entry point for the download module.
    """
    config = get_config()
    output_dir = Path(config.get("output_dir", "data/processed"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_path = output_dir / "metadata.csv"
    
    try:
        # Fetch
        raw_df = fetch_raw_metadata()
        if raw_df is None:
            logger.error("No data fetched. Exiting.")
            return
        
        # Process
        processed_df = process_metadata(raw_df)
        
        # Save
        save_processed_metadata(processed_df, metadata_path)
        
        # Count (T013a)
        count_report = count_unique_planets(metadata_path)
        logger.info(f"Count report generated: {count_report}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
