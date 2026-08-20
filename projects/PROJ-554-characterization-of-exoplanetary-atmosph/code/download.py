"""
Download and process exoplanet spectrum data from NASA Exoplanet Archive.
Implements data acquisition, metadata processing, and planet classification.
"""
import os
import logging
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from config import get_config
from utils import setup_logging, DataFetchError, retry_on_failure
from api_config import QUERY_PARAMS

# Configure logging
logger = logging.getLogger(__name__)

def classify_planet_category(row: pd.Series) -> str:
    """
    Classify planet as 'Hot Jupiter' or 'Temperate Super-Earth' based on
    equilibrium temperature and radius.
    
    Logic:
    - Hot Jupiter: T_eq >= 1000K AND Radius >= 0.8 R_J (approx 9 R_E)
    - Temperate Super-Earth: T_eq < 1000K AND Radius < 2.0 R_J (approx 22 R_E)
      (Note: This is a broad definition to capture rocky/mini-Neptune boundary)
    
    Parameters:
        row: DataFrame row containing 'equilibrium_temperature' and 'radius'
    
    Returns:
        str: Planet category label
    """
    temp = row.get('equilibrium_temperature')
    radius = row.get('radius')
    
    # Handle missing values
    if pd.isna(temp) or pd.isna(radius):
        return 'Unknown'
    
    # Convert radius to Earth radii if in Jupiter radii
    # Assuming input is in Jupiter radii (common for exoplanet archives)
    radius_earth = radius * 11.2  # 1 R_J ≈ 11.2 R_E
    
    if temp >= 1000 and radius_earth >= 9.0:  # Hot Jupiter
        return 'Hot Jupiter'
    elif temp < 1000 and radius_earth < 22.0:  # Temperate Super-Earth (broad)
        return 'Temperate Super-Earth'
    else:
        return 'Other'

@retry_on_failure(max_retries=3, backoff_factor=2)
def fetch_raw_metadata() -> pd.DataFrame:
    """
    Fetch raw metadata from NASA Exoplanet Archive API for Hot Jupiters and Super-Earths.
    
    Returns:
        pd.DataFrame: Raw metadata from API
    
    Raises:
        DataFetchError: If API request fails after retries
    """
    config = get_config()
    api_url = config.get('nasa_archive_url', 'https://exoplanetarchive.ipac.caltech.edu/TAP/sync')
    
    # Build query based on QUERY_PARAMS
    query_parts = []
    for key, value in QUERY_PARAMS.items():
        if isinstance(value, list):
            value_str = ','.join(str(v) for v in value)
            query_parts.append(f"{key} IN ({value_str})")
        else:
            query_parts.append(f"{key} = '{value}'")
    
    query = " AND ".join(query_parts)
    params = {
        'query': f"SELECT * FROM exoplanets WHERE {query}",
        'format': 'json'
    }
    
    logger.info("API request start")
    start_time = time.time()
    
    try:
        response = requests.get(api_url, params=params, timeout=30)
        elapsed = time.time() - start_time
        
        logger.info(f"response status: {response.status_code}, time: {elapsed:.2f}s")
        
        if response.status_code != 200:
            raise DataFetchError(f"API returned status {response.status_code}")
        
        data = response.json()
        if not data or 'data' not in data:
            raise DataFetchError("No data returned from API")
        
        # Convert to DataFrame
        df = pd.DataFrame(data['data'])
        logger.info(f"Download completion: {len(df)} records fetched")
        
        return df
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise DataFetchError(f"Network error: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {str(e)}")
        raise DataFetchError(f"JSON parsing error: {str(e)}")

def process_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process raw metadata to extract required fields and add derived columns.
    
    Parameters:
        df: Raw metadata DataFrame
    
    Returns:
        pd.DataFrame: Processed metadata with required columns
    """
    # Select required columns
    required_cols = [
        'pl_name', 'pl_orbper', 'pl_radj', 'pl_eqt', 'pl_massj',
        'st_met', 'snr', 'resolution', 'disc_fac', 'disc_fac2',
        'pl_controvflag', 'pl_kepflag', 'pl_orbper', 'pl_radj', 'pl_eqt'
    ]
    
    # Filter existing columns
    available_cols = [col for col in required_cols if col in df.columns]
    df_processed = df[available_cols].copy()
    
    # Rename columns to standard names
    rename_map = {
        'pl_name': 'planet_name',
        'pl_radj': 'radius',
        'pl_eqt': 'equilibrium_temperature',
        'pl_massj': 'mass',
        'st_met': 'metallicity',
        'snr': 'snr',
        'resolution': 'resolution'
    }
    
    df_processed = df_processed.rename(columns=rename_map)
    
    # Add planet category
    df_processed['planet_category'] = df_processed.apply(classify_planet_category, axis=1)
    
    # Add instrument and wavelength range (placeholder - would be derived from spectrum files)
    df_processed['instrument'] = 'HST/WFC3'  # Default, would be derived
    df_processed['wavelength_range'] = '1.1-1.7 um'  # Default, would be derived
    
    # Ensure numeric columns
    numeric_cols = ['equilibrium_temperature', 'radius', 'mass', 'metallicity', 'snr', 'resolution']
    for col in numeric_cols:
        if col in df_processed.columns:
            df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
    
    # Fill missing values with reasonable defaults or NaN
    df_processed = df_processed.fillna(np.nan)
    
    return df_processed

def save_processed_metadata(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save processed metadata to CSV file.
    
    Parameters:
        df: Processed metadata DataFrame
        output_path: Path to save CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed metadata to {output_path}")

def count_unique_planets(metadata_path: Path) -> Dict[str, Any]:
    """
    Count unique planets from the saved metadata.csv file.
    
    Parameters:
        metadata_path: Path to metadata.csv file
    
    Returns:
        Dict with 'count' of unique planets
    """
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    df = pd.read_csv(metadata_path)
    unique_count = df['planet_name'].nunique()
    
    result = {
        'count': int(unique_count),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'source_file': str(metadata_path)
    }
    
    return result

def main():
    """Main entry point for download and processing pipeline."""
    config = get_config()
    
    # Set up directories
    raw_dir = Path(config.get('data_raw_dir', 'data/raw'))
    processed_dir = Path(config.get('data_processed_dir', 'data/processed'))
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Fetch raw metadata
    logger.info("Starting metadata fetch")
    raw_df = fetch_raw_metadata()
    
    # Process metadata
    logger.info("Processing metadata")
    processed_df = process_metadata(raw_df)
    
    # Save to processed directory
    metadata_path = processed_dir / 'metadata.csv'
    save_processed_metadata(processed_df, metadata_path)
    
    # Count unique planets
    logger.info("Counting unique planets")
    count_result = count_unique_planets(metadata_path)
    
    # Save count report
    count_report_path = processed_dir / 'count_report.json'
    with open(count_report_path, 'w') as f:
        json.dump(count_result, f, indent=2)
    
    logger.info(f"Count report saved to {count_report_path}")
    logger.info(f"Unique planet count: {count_result['count']}")
    
    return count_result

if __name__ == '__main__':
    setup_logging()
    result = main()
    print(f"Final count: {result['count']}")
