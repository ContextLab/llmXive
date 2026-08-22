"""
NOAA CPC Atmospheric River Catalog Data Ingestion Script.

Fetches AR catalog data from NOAA ERDDAP, applies region filtering for
West Coast NA (35°N-50°N, 120°W-125°W), logs dataset version, and saves
raw downloads with checksums.
"""
import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('noaa_ingestion.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / 'data' / 'raw' / 'noaa-ar'
ERDDAP_BASE_URL = "https://coastwatch.pfeg.noaa.gov/erddap/tabledap"
DATASET_ID = "noaa_cpc_ar_catalog"
REGION_FILTER = {
    'lat_min': 35.0,
    'lat_max': 50.0,
    'lon_min': -125.0,
    'lon_max': -120.0
}

def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_noaa_data() -> pd.DataFrame:
    """
    Fetch NOAA CPC Atmospheric River Catalog data from ERDDAP.

    Returns:
        DataFrame with AR catalog data
    
    Raises:
        RuntimeError: If data fetch fails
    """
    logger.info(f"Fetching NOAA AR data from {ERDDAP_BASE_URL}/{DATASET_ID}")
    
    # Build ERDDAP query
    # Request all columns, filter by date range (last 10 years)
    start_date = "2014-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    # ERDDAP query parameters
    query_params = {
        'time>=': start_date,
        'time<=': end_date,
        '.format': 'csv'
    }
    
    # Construct URL
    query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
    url = f"{ERDDAP_BASE_URL}/{DATASET_ID}.csv?{query_string}"
    
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        
        # Parse CSV
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        
        # Log dataset metadata
        logger.info(f"Retrieved {len(df)} records from NOAA CPC AR Catalog")
        logger.info(f"Data columns: {list(df.columns)}")
        
        # Extract version/release info from response headers or metadata
        # ERDDAP typically includes this in the .info endpoint
        info_url = f"{ERDDAP_BASE_URL}/{DATASET_ID}.info"
        try:
            info_response = requests.get(info_url, timeout=30)
            if info_response.status_code == 200:
                info_data = info_response.json()
                version = info_data.get('info', {}).get('dataset', {}).get('version', 'unknown')
                logger.info(f"Dataset version: {version}")
        except Exception as e:
            logger.warning(f"Could not fetch dataset metadata: {e}")
        
        return df
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch NOAA data: {e}")
        raise RuntimeError(f"NOAA data fetch failed: {e}")
    except Exception as e:
        logger.error(f"Error processing NOAA data: {e}")
        raise RuntimeError(f"NOAA data processing failed: {e}")

def filter_region(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter AR events to West Coast NA region (35°N-50°N, 120°W-125°W).
    
    Args:
        df: DataFrame with AR events including latitude/longitude columns
        
    Returns:
        Filtered DataFrame
    """
    logger.info(f"Applying region filter: {REGION_FILTER}")
    
    # Identify latitude and longitude columns
    lat_col = None
    lon_col = None
    
    for col in df.columns:
        if 'lat' in col.lower() or 'latitude' in col.lower():
            lat_col = col
        elif 'lon' in col.lower() or 'longitude' in col.lower() or 'long' in col.lower():
            lon_col = col
    
    if lat_col is None or lon_col is None:
        # Try common column names
        lat_candidates = ['latitude', 'lat', 'CENTER_LAT', 'start_lat']
        lon_candidates = ['longitude', 'lon', 'CENTER_LON', 'start_lon', 'long']
        
        for candidate in lat_candidates:
            if candidate in df.columns:
                lat_col = candidate
                break
        
        for candidate in lon_candidates:
            if candidate in df.columns:
                lon_col = candidate
                break
    
    if lat_col is None or lon_col is None:
        logger.warning("Could not identify latitude/longitude columns for region filtering")
        logger.warning("Returning unfiltered data")
        return df
    
    logger.info(f"Using {lat_col} and {lon_col} for region filtering")
    
    # Apply region filter
    filtered_df = df[
        (df[lat_col] >= REGION_FILTER['lat_min']) &
        (df[lat_col] <= REGION_FILTER['lat_max']) &
        (df[lon_col] >= REGION_FILTER['lon_min']) &
        (df[lon_col] <= REGION_FILTER['lon_max'])
    ].copy()
    
    logger.info(f"Filtered from {len(df)} to {len(filtered_df)} events in target region")
    
    return filtered_df

def save_raw_data(df: pd.DataFrame, filename: str) -> Path:
    """
    Save raw data to file with checksum.
    
    Args:
        df: DataFrame to save
        filename: Output filename
        
    Returns:
        Path to saved file
    """
    # Ensure directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    filepath = DATA_RAW_DIR / filename
    
    # Save CSV
    df.to_csv(filepath, index=False)
    
    # Calculate and save checksum
    checksum = calculate_sha256(filepath)
    checksum_file = DATA_RAW_DIR / f"{filename}.sha256"
    with open(checksum_file, 'w') as f:
        f.write(f"{checksum}  {filename}\n")
    
    logger.info(f"Saved {len(df)} records to {filepath}")
    logger.info(f"Checksum: {checksum}")
    
    return filepath

def main():
    """Main execution function."""
    logger.info("Starting NOAA CPC Atmospheric River Catalog ingestion")
    
    try:
        # Fetch data
        df = fetch_noaa_data()
        
        if df.empty:
            logger.warning("No data retrieved from NOAA")
            # Create empty file with metadata
            save_raw_data(df, "noaa_ar_catalog_empty.csv")
            return
        
        # Filter by region
        filtered_df = filter_region(df)
        
        # Save raw filtered data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"noaa_ar_catalog_{timestamp}.csv"
        save_raw_data(filtered_df, output_filename)
        
        # Also save unfiltered for reference
        unfiltered_filename = f"noaa_ar_catalog_{timestamp}_unfiltered.csv"
        save_raw_data(df, unfiltered_filename)
        
        logger.info("NOAA AR data ingestion completed successfully")
        
    except Exception as e:
        logger.error(f"NOAA AR data ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
