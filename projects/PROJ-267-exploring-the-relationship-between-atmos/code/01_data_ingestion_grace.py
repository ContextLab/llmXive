"""
GRACE-FO Data Ingestion Script

Fetches GRACE-FO processed mascon solutions from PO.DAAC CMR search API.
Implements region filtering for West Coast NA.
Saves raw downloads with checksums.
"""
import os
import sys
import logging
import hashlib
import json
import time
from pathlib import Path
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/data_ingestion_grace.log')
    ]
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
RAW_DATA_DIR = PROJECT_ROOT / 'data' / 'raw' / 'grace-fo'
LOGS_DIR = PROJECT_ROOT / 'logs'

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Constants
CMR_SEARCH_URL = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"
GRACE_FO_COLLECTION_SHORT_NAME = "GRACEFO_L2_CSR_MASCON_RL06_V2"
REGION_BOUNDS = {
    'lat_min': 35.0,
    'lat_max': 50.0,
    'lon_min': -125.0,
    'lon_max': -120.0
}

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_grace_data() -> pd.DataFrame:
    """
    Fetch GRACE-FO mascon data from PO.DAAC CMR API.
    
    Returns:
        DataFrame with mascon data for the specified region
    """
    logger.info("Fetching GRACE-FO data from PO.DAAC CMR API...")
    
    # Build search parameters
    params = {
        'short_name': GRACE_FO_COLLECTION_SHORT_NAME,
        'point': '42.5,-122.5',  # Center of region
        'temporal': '2018-03-01,2024-12-31',
        'format': 'umm_json',
        'page_size': 2000,
        'token': os.getenv('EARTHDATA_TOKEN', '')
    }
    
    all_granules = []
    page = 0
    max_pages = 10  # Safety limit
    
    while page < max_pages:
        params['page_num'] = page + 1
        try:
            response = requests.get(CMR_SEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'items' not in data or len(data['items']) == 0:
                logger.info("No more granules found.")
                break
            
            all_granules.extend(data['items'])
            logger.info(f"Retrieved page {page + 1}, found {len(data['items'])} granules")
            
            # Check if we have all results
            if len(data['items']) < params['page_size']:
                break
            
            page += 1
            time.sleep(0.5)  # Rate limiting
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from CMR: {e}")
            raise
    
    if not all_granules:
        raise ValueError("No GRACE-FO granules found for the specified criteria")
    
    logger.info(f"Total granules found: {len(all_granules)}")
    
    # Process granules to extract data
    # Note: This is a simplified extraction. In production, you'd need to
    # download and process the actual NetCDF/GeoTIFF files
    processed_data = []
    
    for granule in all_granules:
        try:
            # Extract metadata
            meta = granule.get('umm', {})
            temporal_extent = meta.get('TemporalExtent', {})
            range_date_time = temporal_extent.get('RangeDateTime', {})
            
            start_time = range_date_time.get('BeginningDateTime')
            end_time = range_date_time.get('EndingDateTime')
            
            # Extract spatial bounds if available
            spatial_extent = meta.get('SpatialExtent', {})
            horizontal_spatial_domain = spatial_extent.get('HorizontalSpatialDomain', {})
            geometry = horizontal_spatial_domain.get('Geometry', {})
            bounding_box = geometry.get('BoundingBox', [])
            
            # Convert to DataFrame row
            row = {
                'granule_id': granule.get('meta', {}).get('native-id', ''),
                'start_time': start_time,
                'end_time': end_time,
                'bbox_lat_min': bounding_box[0] if bounding_box else None,
                'bbox_lat_max': bounding_box[1] if bounding_box else None,
                'bbox_lon_min': bounding_box[2] if bounding_box else None,
                'bbox_lon_max': bounding_box[3] if bounding_box else None,
                'url': meta.get('OnlineResources', [{}])[0].get('URL', '') if meta.get('OnlineResources') else ''
            }
            
            processed_data.append(row)
            
        except Exception as e:
            logger.warning(f"Error processing granule: {e}")
            continue
    
    df = pd.DataFrame(processed_data)
    
    # Filter by region
    df = filter_region(df)
    
    logger.info(f"Data filtered to region: {len(df)} granules remaining")
    
    return df

def filter_region(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter data to West Coast NA region (35°N-50°N, 120°W-125°W).
    
    Args:
        df: DataFrame with bounding box information
        
    Returns:
        Filtered DataFrame
    """
    if df.empty:
        return df
    
    # Convert to numeric, coerce errors to NaN
    df['bbox_lat_min'] = pd.to_numeric(df['bbox_lat_min'], errors='coerce')
    df['bbox_lat_max'] = pd.to_numeric(df['bbox_lat_max'], errors='coerce')
    df['bbox_lon_min'] = pd.to_numeric(df['bbox_lon_min'], errors='coerce')
    df['bbox_lon_max'] = pd.to_numeric(df['bbox_lon_max'], errors='coerce')
    
    # Filter for region overlap
    # A granule overlaps if its bounding box intersects with our region
    mask = (
        (df['bbox_lat_max'] >= REGION_BOUNDS['lat_min']) &
        (df['bbox_lat_min'] <= REGION_BOUNDS['lat_max']) &
        (df['bbox_lon_max'] >= REGION_BOUNDS['lon_min']) &
        (df['bbox_lon_min'] <= REGION_BOUNDS['lon_max'])
    )
    
    return df[mask].reset_index(drop=True)

def save_raw_data(df: pd.DataFrame, dataset_version: str) -> Path:
    """
    Save raw data to disk with checksums.
    
    Args:
        df: DataFrame to save
        dataset_version: Version identifier for the dataset
        
    Returns:
        Path to saved file
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"grace-fo-mascon-{dataset_version}-{timestamp}.json"
    file_path = RAW_DATA_DIR / filename
    
    # Save metadata and data
    output_data = {
        'dataset_version': dataset_version,
        'retrieval_timestamp': timestamp,
        'region_bounds': REGION_BOUNDS,
        'data': df.to_dict(orient='records')
    }
    
    with open(file_path, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    # Calculate and save checksum
    checksum = calculate_sha256(file_path)
    checksum_path = RAW_DATA_DIR / f"{filename}.sha256"
    
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {filename}\n")
    
    logger.info(f"Data saved to {file_path}")
    logger.info(f"Checksum: {checksum}")
    
    return file_path

def log_dataset_version(df: pd.DataFrame, dataset_version: str) -> None:
    """
    Log dataset version and metadata per Constitution Principle VI.
    
    Args:
        df: DataFrame with data
        dataset_version: Version identifier
    """
    log_entry = {
        'dataset_version': dataset_version,
        'collection_short_name': GRACE_FO_COLLECTION_SHORT_NAME,
        'retrieval_timestamp': datetime.now().isoformat(),
        'total_granules': len(df),
        'region_bounds': REGION_BOUNDS,
        'api_url': CMR_SEARCH_URL
    }
    
    log_file = RAW_DATA_DIR / 'dataset_metadata.json'
    
    # Load existing logs or create new
    if log_file.exists():
        with open(log_file, 'r') as f:
            logs = json.load(f)
    else:
        logs = []
    
    logs.append(log_entry)
    
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)
    
    logger.info(f"Dataset version logged: {dataset_version}")

def main():
    """Main execution function."""
    logger.info("Starting GRACE-FO data ingestion...")
    
    try:
        # Fetch data
        df = fetch_grace_data()
        
        if df.empty:
            logger.error("No data found after filtering. Exiting.")
            sys.exit(1)
        
        # Determine dataset version (use collection short name + timestamp)
        dataset_version = f"{GRACE_FO_COLLECTION_SHORT_NAME}_RL06"
        
        # Log dataset version
        log_dataset_version(df, dataset_version)
        
        # Save raw data with checksums
        save_raw_data(df, dataset_version)
        
        logger.info("GRACE-FO data ingestion completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during data ingestion: {e}")
        raise

if __name__ == "__main__":
    main()
