"""
NOAA CPC Atmospheric River Catalog Data Ingestion Script (Target Region)

This script fetches the NOAA CPC Atmospheric River Catalog, filters for the Target region
(West Coast NA), and saves the raw data with checksums.

Dependencies: requests, pyyaml, pandas, hashlib
"""

import os
import sys
import logging
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import requests
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "urls.yaml"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "noaa-ar" / "target"

# Target Region Definition (West Coast NA)
# Approximate bounding box for West Coast AR activity
# Latitude: 30°N to 60°N
# Longitude: 130°W to 115°W (converted to negative for standard format)
TARGET_LAT_MIN = 30.0
TARGET_LAT_MAX = 60.0
TARGET_LON_MIN = -130.0
TARGET_LON_MAX = -115.0


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load the configuration YAML file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def fetch_noaa_data(url: str, timeout: int = 60) -> Optional[pd.DataFrame]:
    """
    Fetch the NOAA CPC Atmospheric River Catalog data.

    The NOAA AR Catalog is typically provided as a CSV or JSON file.
    We attempt to fetch it directly. If the URL points to a landing page,
    we attempt to find the direct download link or raise an error.

    Args:
        url: The verified URL from config.
        timeout: Request timeout in seconds.

    Returns:
        pandas DataFrame with the AR catalog data, or None if fetch fails.
    """
    logger.info(f"Fetching NOAA AR Catalog from: {url}")
    try:
        # Try to fetch the content directly
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('Content-Type', '')

        if 'text/csv' in content_type or 'application/json' in content_type or 'text/plain' in content_type:
            # Attempt to parse as CSV first (most common for these catalogs)
            try:
                df = pd.read_csv(pd.io.common.StringIO(response.text))
                logger.info(f"Successfully parsed CSV data. Rows: {len(df)}")
                return df
            except Exception as csv_err:
                logger.warning(f"Failed to parse as CSV: {csv_err}. Trying JSON...")
                try:
                    df = pd.read_json(pd.io.common.StringIO(response.text))
                    logger.info(f"Successfully parsed JSON data. Rows: {len(df)}")
                    return df
                except Exception as json_err:
                    logger.error(f"Failed to parse as JSON: {json_err}")
                    raise ValueError("Could not parse response as CSV or JSON")
        else:
            # Might be a landing page or HTML
            logger.warning(f"Unexpected content type: {content_type}")
            # If it's HTML, we might need to scrape, but for now we fail loudly
            # as per constraint: "Never fabricate... if no real source is reachable, return failed"
            # However, we assume the URL in config/urls.yaml is the direct data link.
            # If it's a landing page, we raise an error to be handled by the runner.
            raise ValueError(f"URL returned unexpected content type: {content_type}. "
                             f"Expected CSV/JSON direct data link.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching NOAA data: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing NOAA data: {e}")
        raise


def filter_region(df: pd.DataFrame, region_type: str = 'target') -> pd.DataFrame:
    """
    Filter the DataFrame based on the region definition.

    For 'target', we use the West Coast NA bounding box.
    For 'control', we would use the East Coast NA bounding box (not implemented here).

    Args:
        df: Input DataFrame.
        region_type: 'target' or 'control'.

    Returns:
        Filtered DataFrame.
    """
    if region_type != 'target':
        raise NotImplementedError(f"Region filtering for '{region_type}' is not implemented in this script.")

    # Identify latitude and longitude columns
    # NOAA AR catalog typically uses 'latitude'/'longitude' or 'lat'/'lon'
    lat_col = None
    lon_col = None

    for col in df.columns:
        if col.lower() in ['latitude', 'lat']:
            lat_col = col
        elif col.lower() in ['longitude', 'lon']:
            lon_col = col

    if lat_col is None or lon_col is None:
        # If specific columns not found, try to infer or raise error
        # Some datasets might have 'center_lat', 'center_lon'
        for col in df.columns:
            if 'lat' in col.lower():
                lat_col = col
            if 'lon' in col.lower():
                lon_col = col

    if lat_col is None or lon_col is None:
        logger.warning("Could not identify latitude/longitude columns. Returning full dataset.")
        return df

    logger.info(f"Filtering by target region: Lat [{TARGET_LAT_MIN}, {TARGET_LAT_MAX}], "
                f"Lon [{TARGET_LON_MIN}, {TARGET_LON_MAX}]")

    mask = (
        (df[lat_col] >= TARGET_LAT_MIN) &
        (df[lat_col] <= TARGET_LAT_MAX) &
        (df[lon_col] >= TARGET_LON_MIN) &
        (df[lon_col] <= TARGET_LON_MAX)
    )

    filtered_df = df[mask].reset_index(drop=True)
    logger.info(f"Filtered dataset size: {len(filtered_df)} rows (from {len(df)})")

    return filtered_df


def save_raw_data(df: pd.DataFrame, output_dir: Path) -> str:
    """
    Save the raw data to a CSV file and return the file path.
    Also creates a JSON metadata file.

    Args:
        df: DataFrame to save.
        output_dir: Directory to save files.

    Returns:
        Path to the saved CSV file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"noaa_ar_catalog_target_{timestamp}.csv"
    file_path = output_dir / filename

    df.to_csv(file_path, index=False)
    logger.info(f"Saved raw data to: {file_path}")

    # Save metadata
    metadata = {
        "source": "NOAA CPC Atmospheric River Catalog",
        "region": "target",
        "timestamp": timestamp,
        "row_count": len(df),
        "columns": list(df.columns)
    }
    metadata_path = output_dir / f"noaa_ar_catalog_target_{timestamp}.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    return str(file_path)


def log_dataset_version(df: pd.DataFrame, source_url: str) -> None:
    """Log dataset version/release date information."""
    # Attempt to extract version info from metadata or column names if available
    # For now, we log the row count and source
    logger.info(f"Dataset loaded from: {source_url}")
    logger.info(f"Total records: {len(df)}")
    logger.info(f"Columns: {list(df.columns)}")


def main():
    """Main entry point for the NOAA data ingestion script."""
    logger.info("=== NOAA CPC Atmospheric River Catalog Ingestion (Target) Start ===")

    try:
        # 1. Load Configuration
        config = load_config(CONFIG_PATH)
        if 'noaa_ar_catalog' not in config:
            raise KeyError("Key 'noaa_ar_catalog' not found in config/urls.yaml")

        source_url = config['noaa_ar_catalog']
        logger.info(f"Using verified URL: {source_url}")

        # 2. Fetch Data
        df = fetch_noaa_data(source_url)
        if df is None or df.empty:
            raise ValueError("Fetched data is empty.")

        # 3. Log Dataset Version
        log_dataset_version(df, source_url)

        # 4. Filter Region
        filtered_df = filter_region(df, region_type='target')
        if filtered_df.empty:
            logger.warning("No data found in the target region. Saving empty dataset.")

        # 5. Save Raw Data
        output_path = save_raw_data(filtered_df, RAW_DATA_DIR)

        # 6. Calculate and Log Checksum
        checksum = calculate_sha256(Path(output_path))
        logger.info(f"SHA-256 Checksum: {checksum}")

        # Save checksum to a sidecar file
        checksum_path = Path(output_path).with_suffix('.sha256')
        with open(checksum_path, 'w') as f:
            f.write(f"{checksum}  {Path(output_path).name}\n")

        logger.info("=== NOAA CPC Atmospheric River Catalog Ingestion (Target) Complete ===")
        return 0

    except Exception as e:
        logger.critical(f"NOAA Ingestion failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())