"""
NOAA CPC Atmospheric River Catalog Data Ingestion Script.

Fetches AR catalog data from NOAA ERDDAP, filters for West Coast NA region,
logs dataset metadata, and saves raw downloads with checksums.
"""
import os
import sys
import logging
import hashlib
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Project root path (assumed to be the parent of 'code')
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "noaa-ar"
OUTPUT_FILE = DATA_RAW_DIR / "ar_catalog_raw.json"
METADATA_FILE = DATA_RAW_DIR / "dataset_metadata.json"

# NOAA ERDDAP endpoint for AR Catalog
ERDDAP_URL = "https://coastwatch.pfeg.noaa.gov/erddap/tabledap/ar_catalog.html"
# Specific query for West Coast NA region (35N-50N, 125W-120W)
# We fetch all data and filter in Python to ensure we get the full context for logging
QUERY_URL = f"{ERDDAP_URL}?date,latitude,longitude,peak_intensity,duration,area,ar_type"

# Region definition
LAT_MIN, LAT_MAX = 35.0, 50.0
LON_MIN, LON_MAX = -125.0, -120.0  # 120W to 125W (negative for W)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_noaa_data() -> list:
    """
    Fetch NOAA CPC Atmospheric River Catalog data from ERDDAP.
    Returns a list of dictionaries representing the records.
    """
    logger.info(f"Fetching data from {ERDDAP_URL}...")
    try:
        # ERDDAP tabledap supports CSV format for easier parsing
        csv_url = f"{ERDDAP_URL}?date,latitude,longitude,peak_intensity,duration,area,ar_type&.csv"
        
        req = urllib.request.Request(csv_url)
        req.add_header('User-Agent', 'Mozilla/5.0 (llmXive Research Agent)')
        
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status != 200:
                raise RuntimeError(f"Failed to fetch data: HTTP {response.status}")
            
            content = response.read().decode('utf-8')
            lines = content.strip().split('\n')
            
            if len(lines) < 2:
                logger.warning("No data rows found in response.")
                return []

            # Parse CSV header
            header = [h.strip() for h in lines[0].split(',')]
            
            records = []
            for line in lines[1:]:
                if not line.strip():
                    continue
                values = [v.strip() for v in line.split(',')]
                if len(values) != len(header):
                    logger.warning(f"Skipping malformed row: {line}")
                    continue
                
                row_dict = dict(zip(header, values))
                records.append(row_dict)
            
            logger.info(f"Successfully fetched {len(records)} records.")
            return records

    except urllib.error.URLError as e:
        logger.error(f"Network error fetching NOAA data: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing NOAA data: {e}")
        raise

def filter_region(records: list) -> list:
    """
    Filter records to include only those within the West Coast NA region.
    Region: 35N-50N, 125W-120W.
    """
    logger.info(f"Filtering for region: Lat [{LAT_MIN}, {LAT_MAX}], Lon [{LON_MIN}, {LON_MAX}]")
    filtered = []
    skipped = 0

    for record in records:
        try:
            lat = float(record.get('latitude', 0))
            lon = float(record.get('longitude', 0))
            
            # Check bounds
            if LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX:
                filtered.append(record)
            else:
                skipped += 1
        except ValueError:
            skipped += 1
            logger.debug(f"Skipping record with invalid coordinates: {record}")

    logger.info(f"Filtered {len(filtered)} records. Skipped {skipped} outside region.")
    return filtered

def save_raw_data(data: list, output_path: Path):
    """Save raw data to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Raw data saved to {output_path}")

def log_dataset_version(data: list, metadata_path: Path):
    """
    Log dataset version, release date, and other metadata.
    Since ERDDAP doesn't always expose a specific 'version' string in the feed,
    we log the fetch timestamp and the count of records as a proxy for versioning.
    """
    metadata = {
        "source": "NOAA CPC Atmospheric River Catalog",
        "url": ERDDAP_URL,
        "fetch_timestamp": datetime.utcnow().isoformat() + "Z",
        "total_records_fetched": len(data),
        "region_filter": {
            "lat_min": LAT_MIN,
            "lat_max": LAT_MAX,
            "lon_min": LON_MIN,
            "lon_max": LON_MAX
        },
        "note": "Dataset version/release date is implicit in the fetch timestamp. "
                "For precise versioning, consult the NOAA CPC AR Catalog documentation."
    }
    
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Dataset metadata logged to {metadata_path}")

def main():
    """Main entry point for the script."""
    logger.info("Starting NOAA AR Data Ingestion (T016)...")
    
    try:
        # 1. Fetch Data
        raw_data = fetch_noaa_data()
        
        if not raw_data:
            logger.error("No data retrieved. Exiting.")
            sys.exit(1)

        # 2. Filter Region
        filtered_data = filter_region(raw_data)
        
        if not filtered_data:
            logger.warning("No data found in the specified region. Saving empty result.")
        
        # 3. Save Raw Data (filtered) to disk
        save_raw_data(filtered_data, OUTPUT_FILE)
        
        # 4. Calculate Checksum
        checksum = calculate_sha256(OUTPUT_FILE)
        logger.info(f"Checksum (SHA256): {checksum}")
        
        # 5. Log Metadata
        log_dataset_version(filtered_data, METADATA_FILE)
        
        # Update metadata with checksum
        metadata_path = METADATA_FILE
        with open(metadata_path, 'r') as f:
            meta = json.load(f)
        meta["checksum_sha256"] = checksum
        with open(metadata_path, 'w') as f:
            json.dump(meta, f, indent=2)
        
        logger.info("T016 NOAA Data Ingestion completed successfully.")
        
    except Exception as e:
        logger.error(f"Fatal error in T016: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
