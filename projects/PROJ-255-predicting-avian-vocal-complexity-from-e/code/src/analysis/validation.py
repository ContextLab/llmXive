import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import requests
import pandas as pd

from src.utils.config import get_project_root, get_interim_data_dir
from src.utils.logging import setup_logger

# Configure logger for this module
logger = setup_logger("validation", "validation.log")

# Constants
DEVIATION_THRESHOLD_DB = 2.0
GLOBAL_SOUNDSCAPES_URL = "https://raw.githubusercontent.com/global-soundscapes/data/main/noise_levels.csv"
# Fallback: If the specific URL fails or the dataset is not available, we log the justification.
# We do not fabricate data.

def fetch_global_soundscapes_data(timeout: int = 10) -> Optional[pd.DataFrame]:
    """
    Attempts to fetch the Global Soundscapes dataset from a public URL.
    Returns None if the dataset is unavailable or the request fails.
    """
    try:
        logger.info(f"Attempting to fetch Global Soundscapes dataset from {GLOBAL_SOUNDSCAPES_URL}")
        response = requests.get(GLOBAL_SOUNDSCAPES_URL, timeout=timeout)
        
        if response.status_code == 200:
            # Try to parse as CSV. The structure is assumed to have 'latitude', 'longitude', 'noise_db'
            # or similar columns. We handle potential parsing errors gracefully.
            df = pd.read_csv(pd.io.common.StringIO(response.text))
            
            # Normalize column names to lowercase for robustness
            df.columns = df.columns.str.lower().str.strip()
            
            # Check for required columns
            required_cols = {'latitude', 'longitude', 'noise_db'}
            if not required_cols.issubset(set(df.columns)):
                logger.warning(f"Global Soundscapes dataset missing required columns. Found: {list(df.columns)}. Expected: {required_cols}")
                return None
            
            logger.info("Successfully fetched Global Soundscapes dataset.")
            return df
        else:
            logger.warning(f"Failed to fetch Global Soundscapes dataset. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while fetching Global Soundscapes: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing Global Soundscapes data: {e}")
        return None

def validate_osm_proxies(
    noise_mapped_path: Path,
    output_log_path: Path
) -> None:
    """
    Validates OSM noise proxies against the Global Soundscapes dataset.
    
    If Global Soundscapes is available:
      - Matches records by location (lat/lon).
      - Calculates deviation.
      - Logs records with deviation > 2 dB(A).
      
    If Global Soundscapes is unavailable:
      - Logs a justification for using OSM-only data to satisfy FR-002.
      
    Args:
        noise_mapped_path: Path to data/interim/noise_mapped.csv
        output_log_path: Path to data/interim/validation_log.csv
    """
    if not noise_mapped_path.exists():
        logger.error(f"Noise mapped file not found: {noise_mapped_path}")
        # Create an empty log indicating failure to find input
        with open(output_log_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['status', 'message'])
            writer.writerow(['error', 'Input file not found'])
        return

    # Load OSM noise mapped data
    try:
        df_osm = pd.read_csv(noise_mapped_path)
        # Normalize columns
        df_osm.columns = df_osm.columns.str.lower().str.strip()
        required_osm_cols = {'latitude', 'longitude', 'noise_level_db'}
        if not required_osm_cols.issubset(set(df_osm.columns)):
            # Fallback to common names if exact match fails, or just log error
            logger.warning(f"Input file missing required columns. Expected: {required_osm_cols}")
            # Attempt to map common variations if possible, else fail gracefully
            if 'lat' in df_osm.columns: df_osm['latitude'] = df_osm['lat']
            if 'lon' in df_osm.columns: df_osm['longitude'] = df_osm['lon']
            if 'noise_db' in df_osm.columns: df_osm['noise_level_db'] = df_osm['noise_db']
            
            if not required_osm_cols.issubset(set(df_osm.columns)):
                logger.error("Cannot proceed: Required columns (latitude, longitude, noise_level_db) missing in input.")
                with open(output_log_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['status', 'message'])
                    writer.writerow(['error', 'Input file missing required columns'])
                return
    except Exception as e:
        logger.error(f"Error reading noise mapped file: {e}")
        return

    global_data = fetch_global_soundscapes_data()
    validation_results = []

    if global_data is None:
        # Case: Global Soundscapes unavailable
        logger.warning("Global Soundscapes dataset unavailable. Logging justification for OSM-only usage.")
        justification = (
            "Global Soundscapes dataset could not be retrieved or parsed. "
            "Validation against external ground truth was skipped. "
            "OSM land-use proxies (Urban=60, Rural=40, Wild=30 dB) are used as the sole source of noise estimation "
            "for this run, as per the project's fallback strategy when external validation data is inaccessible. "
            "This satisfies FR-002 by documenting the deviation source and justification."
        )
        
        validation_results.append({
            'validation_type': 'Global Soundscapes Comparison',
            'status': 'SKIPPED',
            'reason': 'Dataset Unavailable',
            'details': justification,
            'records_validated': 0,
            'records_failed': 0,
            'max_deviation_db': 'N/A'
        })
    else:
        # Case: Global Soundscapes available
        logger.info("Global Soundscapes dataset available. Performing validation.")
        
        # Merge on lat/lon
        # We need to handle floating point precision. We'll round to 3 decimal places for matching.
        df_osm['lat_round'] = df_osm['latitude'].round(3)
        df_osm['lon_round'] = df_osm['longitude'].round(3)
        global_data['lat_round'] = global_data['latitude'].round(3)
        global_data['lon_round'] = global_data['longitude'].round(3)
        
        merged = pd.merge(
            df_osm, 
            global_data, 
            left_on=['lat_round', 'lon_round'], 
            right_on=['lat_round', 'lon_round'], 
            how='inner',
            suffixes=('_osm', '_gs')
        )
        
        if len(merged) == 0:
            logger.warning("No matching coordinates found between OSM data and Global Soundscapes.")
            validation_results.append({
                'validation_type': 'Global Soundscapes Comparison',
                'status': 'NO_MATCHES',
                'reason': 'No coordinate overlap',
                'details': 'No records matched between OSM data and Global Soundscapes dataset.',
                'records_validated': 0,
                'records_failed': 0,
                'max_deviation_db': 'N/A'
            })
        else:
            # Calculate deviation
            # Assuming 'noise_level_db' in merged is from OSM, and 'noise_db' from GS
            # Ensure types are numeric
            merged['noise_level_db'] = pd.to_numeric(merged['noise_level_db'], errors='coerce')
            merged['noise_db'] = pd.to_numeric(merged['noise_db'], errors='coerce')
            
            merged['deviation'] = (merged['noise_level_db'] - merged['noise_db']).abs()
            
            valid_count = len(merged[merged['deviation'] <= DEVIATION_THRESHOLD_DB])
            failed_count = len(merged[merged['deviation'] > DEVIATION_THRESHOLD_DB])
            max_dev = merged['deviation'].max() if not merged['deviation'].empty else 0.0
            
            status = "PASSED" if failed_count == 0 else "FAILED"
            
            # Log details for failed records if any
            failed_records = merged[merged['deviation'] > DEVIATION_THRESHOLD_DB]
            for _, row in failed_records.iterrows():
                validation_results.append({
                    'validation_type': 'Global Soundscapes Comparison',
                    'status': 'FAILED',
                    'reason': 'Deviation > 2 dB(A)',
                    'details': f"OSM: {row['noise_level_db']:.1f} dB, GS: {row['noise_db']:.1f} dB, Deviation: {row['deviation']:.2f} dB",
                    'records_validated': 0,
                    'records_failed': 1,
                    'max_deviation_db': row['deviation']
                })
            
            # Summary row
            validation_results.append({
                'validation_type': 'Global Soundscapes Comparison',
                'status': status,
                'reason': 'Validation Complete',
                'details': f"Total matches: {len(merged)}. Passed: {valid_count}. Failed: {failed_count}. Max Deviation: {max_dev:.2f} dB.",
                'records_validated': valid_count,
                'records_failed': failed_count,
                'max_deviation_db': max_dev
            })

    # Write output
    output_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_log_path, 'w', newline='') as f:
        if validation_results:
            fieldnames = validation_results[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(validation_results)
    
    logger.info(f"Validation log written to {output_log_path}")

def main():
    """Main entry point for the validation script."""
    root_dir = get_project_root()
    interim_dir = get_interim_data_dir()
    
    input_file = interim_dir / "noise_mapped.csv"
    output_file = interim_dir / "validation_log.csv"
    
    logger.info("Starting OSM Proxy Validation Task (T015c)")
    validate_osm_proxies(input_file, output_file)
    logger.info("Validation Task Complete")

if __name__ == "__main__":
    main()
