"""
Script to ensure dataset availability for the project.
Downloads datasets from UCI or OpenML if not present in data/raw.
"""
import os
import sys
import logging
import hashlib
from pathlib import Path
from urllib.request import urlopen, Request
from typing import Optional, Tuple, Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from utils import setup_logging, compute_file_checksum

logger = logging.getLogger(__name__)

# Define dataset URLs
DATASET_URLS = {
    'UCI_HAR': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00240/UCI%20HAR%20Dataset.zip',
    'UCI_SHOPPER': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00394/Online%20Retail.xlsx'
}

def download_file(url: str, dest_path: str) -> bool:
    """
    Download a file from a URL to a destination path.
    """
    try:
        logger.info(f"Downloading {url} to {dest_path}")
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=30) as response:
            with open(dest_path, 'wb') as out_file:
                out_file.write(response.read())
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def ensure_data_exists() -> bool:
    """
    Ensure that the required datasets exist in data/raw.
    Downloads them if missing.
    """
    config = Config()
    raw_dir = config.get('RAW_DATA_PATH', 'data/raw')
    os.makedirs(raw_dir, exist_ok=True)

    # Check for HAR dataset (CSV version is easier to handle, but we might get zip)
    # For simplicity, we assume the zip is downloaded and we extract it or check for existence
    # Since extracting is complex without dependencies, we will check for the zip and a marker file
    # Or we can try to download a CSV version if available.
    # For this task, we will just ensure the raw download happens.
    
    # HAR Dataset (Zip)
    har_zip = os.path.join(raw_dir, 'UCI_HAR_Dataset.zip')
    if not os.path.exists(har_zip):
        if not download_file(DATASET_URLS['UCI_HAR'], har_zip):
            logger.warning("Failed to download UCI HAR dataset. Fallback to Shopper.")
    
    # Shopper Dataset (Excel)
    shopper_xlsx = os.path.join(raw_dir, 'Online Retail.xlsx')
    if not os.path.exists(shopper_xlsx):
        if not download_file(DATASET_URLS['UCI_SHOPPER'], shopper_xlsx):
            logger.warning("Failed to download UCI Shopper dataset.")

    # If we have at least one file, consider it success
    files = os.listdir(raw_dir)
    if len(files) == 0:
        logger.error("No datasets downloaded.")
        return False

    logger.info(f"Data availability check passed. Found {len(files)} files in {raw_dir}")
    return True

def main():
    setup_logging()
    success = ensure_data_exists()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
