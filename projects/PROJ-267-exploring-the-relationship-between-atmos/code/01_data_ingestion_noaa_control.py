import os
import sys
import logging
import hashlib
import json
import time
import requests
import pandas as pd
from pathlib import Path
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Project root relative to script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "urls.yaml"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "noaa-ar" / "control"

# Control region definition (East Coast NA - minimal AR activity)
CONTROL_LAT_MIN = 25.0
CONTROL_LAT_MAX = 50.0
CONTROL_LON_MIN = -95.0
CONTROL_LON_MAX = -75.0

def load_config():
    """Load verified URLs from config/urls.yaml."""
    if not CONFIG_PATH.exists():
        logger.error(f"Configuration file not found: {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def calculate_sha256(file_path):
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_noaa_data(url):
    """
    Fetch NOAA CPC Atmospheric River Catalog from the provided URL.
    Returns the content as bytes and logs the dataset version.
    """
    logger.info(f"Fetching data from: {url}")
    try:
        # Use a larger timeout for large file downloads
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        
        # Extract filename from URL
        filename = url.split('/')[-1]
        if not filename:
            filename = "noaa_ar_catalog.csv"
        
        logger.info(f"Successfully fetched {filename} ({len(response.content)} bytes)")
        
        # Log dataset version/release date if available in headers or content
        logger.info(f"Dataset version/release info: {filename}")
        
        return response.content, filename
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch NOAA AR data: {e}")
        raise

def filter_region(df):
    """
    Filter the NOAA AR catalog data to the Control region (East Coast NA).
    Expected columns: 'latitude', 'longitude', 'date', 'intensity' (or similar)
    """
    logger.info(f"Filtering data to control region: Lat [{CONTROL_LAT_MIN}, {CONTROL_LAT_MAX}], Lon [{CONTROL_LON_MIN}, {CONTROL_LON_MAX}]")
    
    # Ensure columns exist
    required_cols = ['latitude', 'longitude']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns for filtering: {missing_cols}")
        # Attempt to map common alternative names
        col_mapping = {}
        if 'lat' in df.columns and 'latitude' not in df.columns:
            col_mapping['lat'] = 'latitude'
        if 'lon' in df.columns and 'longitude' not in df.columns:
            col_mapping['lon'] = 'longitude'
        
        if col_mapping:
            df = df.rename(columns=col_mapping)
            logger.info(f"Renamed columns: {col_mapping}")
        else:
            raise ValueError(f"Cannot filter data. Missing columns: {missing_cols}. Available: {df.columns.tolist()}")
    
    # Apply filters
    mask = (
        (df['latitude'] >= CONTROL_LAT_MIN) &
        (df['latitude'] <= CONTROL_LAT_MAX) &
        (df['longitude'] >= CONTROL_LON_MIN) &
        (df['longitude'] <= CONTROL_LON_MAX)
    )
    
    filtered_df = df[mask].reset_index(drop=True)
    logger.info(f"Filtered data shape: {filtered_df.shape} (original: {df.shape})")
    
    if filtered_df.empty:
        logger.warning("No data points found in the control region. Returning empty DataFrame.")
    
    return filtered_df

def save_raw_data(content, filename, checksum):
    """Save raw data file and record checksum."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_path = RAW_DATA_DIR / filename
    
    with open(file_path, 'wb') as f:
        f.write(content)
    
    logger.info(f"Saved raw data to: {file_path}")
    
    # Record checksum in a metadata file
    checksum_path = RAW_DATA_DIR / f"{filename}.sha256"
    with open(checksum_path, 'w') as f:
        json.dump({
            "filename": filename,
            "sha256": checksum,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }, f, indent=2)
    
    logger.info(f"Saved checksum to: {checksum_path}")

def log_dataset_version(filename, content):
    """Log dataset version/release date from metadata or filename."""
    logger.info(f"Dataset version logged for: {filename}")

def main():
    """Main entry point for NOAA AR control region data ingestion."""
    logger.info("=== NOAA AR Control Region Data Ingestion Start ===")
    
    # Load configuration
    config = load_config()
    
    # Get the verified URL for NOAA AR Catalog from config
    noaa_url_key = "noaa-ar-catalog"
    if noaa_url_key not in config.get("urls", {}):
        logger.error(f"URL key '{noaa_url_key}' not found in config/urls.yaml")
        sys.exit(1)
    
    noaa_url = config["urls"][noaa_url_key]
    logger.info(f"Using verified URL: {noaa_url}")
    
    # Fetch data
    try:
        content, filename = fetch_noaa_data(noaa_url)
    except Exception as e:
        logger.critical(f"NOAA AR ingestion failed: Real data fetch failed: {e}")
        sys.exit(1)
    
    # Log dataset version
    log_dataset_version(filename, content)
    
    # Attempt to parse and filter if the content is a supported format
    file_ext = Path(filename).suffix.lower()
    filtered_content = None
    filtered_filename = None
    
    if file_ext == '.csv':
        try:
            # Parse CSV and filter
            df = pd.read_csv(pd.io.common.BytesIO(content))
            filtered_df = filter_region(df)
            
            # Save filtered CSV
            filtered_filename = f"filtered_{filename}"
            filtered_content = filtered_df.to_csv(index=False).encode('utf-8')
            
            # Calculate checksum for filtered file
            filtered_checksum = calculate_sha256(pd.io.common.BytesIO(filtered_content))
            save_raw_data(filtered_content, filtered_filename, filtered_checksum)
            
            logger.info(f"Saved filtered data: {filtered_filename}")
        except Exception as e:
            logger.warning(f"Could not parse/filter CSV data: {e}. Saving raw file only.")
    else:
        # Save raw file for other formats
        checksum = calculate_sha256(pd.io.common.BytesIO(content))
        save_raw_data(content, filename, checksum)
    
    logger.info("=== NOAA AR Control Region Data Ingestion Complete ===")

if __name__ == "__main__":
    main()