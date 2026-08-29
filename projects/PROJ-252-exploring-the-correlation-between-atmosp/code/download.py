import os
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import requests
import pandas as pd
import yaml

from utils.logging import setup_logger, get_logger

# Configure logging
logger = setup_logger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from data/processed/config.yaml."""
    config_path = Path("data/processed/config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def verify_deviations() -> None:
    """Verify that deviation records exist in docs/deviations.md."""
    deviations_path = Path("docs/deviations.md")
    if not deviations_path.exists():
        logger.warning(f"Deviation file not found at {deviations_path}. Proceeding with caution.")
        return
    
    with open(deviations_path, 'r') as f:
        content = f.read()
    
    # Check for DEV-001 (Global Data Block)
    if "DEV-001" not in content:
        logger.warning("DEV-001 (Global Data Block) deviation record not found.")
    else:
        logger.info("DEV-001 deviation record found.")

def check_noaa_availability() -> bool:
    """
    Check for the absence of verified global NOAA NCEP/NCAR sources in plan.md.
    Returns True if the source is ABSENT (meaning we must block download),
    False if a verified source is present.
    """
    plan_path = Path("specs/001-exploring-the-correlation-between-atmosp/plan.md")
    if not plan_path.exists():
        logger.warning("plan.md not found. Assuming NOAA source is absent.")
        return True  # Absent -> Block
    
    with open(plan_path, 'r') as f:
        plan_content = f.read()
    
    # Look for a "Verified Datasets" block that explicitly lists NOAA
    # If we don't find a clear verification, we assume it's blocked per FR-001
    if "NOAA" in plan_content and "Verified" in plan_content:
        # Basic heuristic: if both words appear near each other in a list context
        lines = plan_content.split('\n')
        for i, line in enumerate(lines):
            if "Verified" in line and i+1 < len(lines) and "NOAA" in lines[i+1]:
                logger.info("Verified NOAA source found in plan.md. Download permitted.")
                return False
    
    logger.info("Verified NOAA NCEP/NCAR source NOT found in plan.md. Blocking global download per FR-001.")
    return True  # Absent -> Block

def fetch_usgs_data(magnitude: float = 4.0, depth: float = 70.0, 
                    start_date: str = "2018-01-01", end_date: str = "2018-12-31",
                    region: str = "Alaska") -> pd.DataFrame:
    """
    Fetch earthquake data from USGS API for the specified region and criteria.
    """
    base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "minmagnitude": magnitude,
        "maxdepth": depth,
        "starttime": start_date,
        "endtime": end_date,
        "orderby": "time"
    }
    
    # For Alaska, we use a bounding box or region filter
    # Alaska bounds approx: lat 51-71, lon -172 to -129
    if region == "Alaska":
        params["minlatitude"] = 51.0
        params["maxlatitude"] = 71.0
        params["minlongitude"] = -172.0
        params["maxlongitude"] = -129.0

    logger.info(f"Fetching USGS data for {region} ({start_date} to {end_date})...")
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        features = data.get('features', [])
        if not features:
            logger.warning("No earthquake features found in the response.")
            return pd.DataFrame()
        
        # Flatten GeoJSON features into a DataFrame
        records = []
        for feat in features:
            props = feat.get('properties', {})
            geom = feat.get('geometry', {})
            coords = geom.get('coordinates', [0, 0, 0])
            
            record = {
                'event_id': props.get('id'),
                'timestamp': props.get('time'),
                'magnitude': props.get('mag'),
                'depth': coords[2],
                'lon': coords[0],
                'lat': coords[1],
                'place': props.get('place'),
                'url': props.get('url')
            }
            records.append(record)
        
        df = pd.DataFrame(records)
        logger.info(f"Fetched {len(df)} earthquake events.")
        return df
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch USGS data: {e}")
        raise

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_raw_data(data: pd.DataFrame, output_path: Path, data_type: str = "usgs") -> str:
    """
    Save raw data to disk and calculate its checksum for immutability checks.
    Returns the checksum.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if data_type == "usgs":
        # Save as JSON to preserve raw structure
        json_path = output_path.with_suffix('.json')
        data.to_json(json_path, orient='records', indent=2)
        checksum = calculate_checksum(json_path)
        logger.info(f"Saved raw USGS data to {json_path} (Checksum: {checksum[:16]}...)")
        return checksum
    else:
        # Default to CSV
        csv_path = output_path.with_suffix('.csv')
        data.to_csv(csv_path, index=False)
        checksum = calculate_checksum(csv_path)
        logger.info(f"Saved raw data to {csv_path} (Checksum: {checksum[:16]}...)")
        return checksum

def verify_data_integrity(file_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """
    Verify the integrity of a file by recalculating its checksum.
    If expected_checksum is provided, compare against it.
    Returns True if valid, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found for integrity check: {file_path}")
        return False
    
    actual_checksum = calculate_checksum(file_path)
    logger.info(f"Integrity check for {file_path}: {actual_checksum[:16]}...")
    
    if expected_checksum:
        if actual_checksum == expected_checksum:
            logger.info("Integrity check PASSED: Checksum matches.")
            return True
        else:
            logger.error(f"Integrity check FAILED: Expected {expected_checksum[:16]}..., got {actual_checksum[:16]}...")
            return False
    return True

def process_test_subset(df: pd.DataFrame, expected_count: int = 12) -> pd.DataFrame:
    """
    Filter the fetched data to the specific test subset (2018 Alaska, M>=4.0).
    Ensures we have the expected number of events for the pilot.
    """
    # The fetch_usgs_data already filters by magnitude and region.
    # We just need to ensure we have the right count or log if we don't.
    if len(df) != expected_count:
        logger.warning(f"Expected {expected_count} events, but found {len(df)}. "
                       f"This may indicate a change in the test dataset or criteria.")
    return df.head(expected_count)

def main():
    """
    Main entry point for the download pipeline (T011a + T012).
    1. Verify deviations (FR-001).
    2. Check NOAA availability (Block if absent).
    3. Fetch USGS data.
    4. Process test subset.
    5. Save raw data with checksumming (T012).
    6. Verify integrity.
    """
    logger.info("Starting download pipeline.")
    
    # Load config
    try:
        config = load_config()
    except FileNotFoundError as e:
        logger.critical(str(e))
        return 1
    
    expected_count = config.get('expected_earthquake_count', 12)
    
    # T011a: Verify Deviations and Block Global Data
    verify_deviations()
    
    # Check if global NOAA data is available (it shouldn't be per FR-001)
    noaa_blocked = check_noaa_availability()
    if noaa_blocked:
        logger.info("Global NOAA NCEP/NCAR download is BLOCKED per FR-001 (DEV-001).")
        logger.info("Proceeding with USGS test subset only.")
    else:
        logger.warning("Verified NOAA source detected. This deviates from pilot scope FR-001.")
    
    # Fetch USGS Data
    try:
        df_usgs = fetch_usgs_data(
            magnitude=4.0,
            depth=70.0,
            start_date="2018-01-01",
            end_date="2018-12-31",
            region="Alaska"
        )
    except Exception as e:
        logger.critical(f"Failed to fetch USGS data: {e}")
        return 1
    
    if df_usgs.empty:
        logger.critical("No earthquake data retrieved.")
        return 1
    
    # Process Test Subset
    df_subset = process_test_subset(df_usgs, expected_count)
    
    # T012: Save Raw Data with Checksumming
    raw_output_path = Path("data/raw/usgs_test_subset")
    checksum = save_raw_data(df_subset, raw_output_path, data_type="usgs")
    
    # Verify Integrity (Self-check immediately after save)
    # We reconstruct the path to the saved file
    saved_file = raw_output_path.with_suffix('.json')
    if not verify_data_integrity(saved_file, checksum):
        logger.critical("Data integrity verification failed immediately after save.")
        return 1
    
    logger.info("Download pipeline completed successfully.")
    logger.info(f"Raw data saved to {saved_file} with checksum {checksum}")
    return 0

if __name__ == "__main__":
    exit(main())