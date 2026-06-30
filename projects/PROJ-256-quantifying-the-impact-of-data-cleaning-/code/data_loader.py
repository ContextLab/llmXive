"""
Data acquisition module for the Quantifying the Impact of Data Cleaning project.

Implements logic to download datasets from OpenML (primary) and UCI (fallback),
validate data integrity, and compute checksums.
"""
import os
import json
import logging
import hashlib
from typing import Optional, Tuple, Dict, Any, List
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import json
import pandas as pd
import numpy as np
from io import StringIO
import zipfile
import tempfile
import shutil

from config import get_config
from utils import compute_file_checksum, setup_logging, pin_random_seed

# Configure logger for this module
logger = logging.getLogger(__name__)

# Dataset URLs
OPENML_DATASET_ID = "554"  # OpenML Small Datasets collection example (Adult or similar small dataset)
# Fallback URLs
UCI_HAR_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00240/UCI%20HAR%20Dataset.zip"
UCI_SHOPPER_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00523/Shopper%20Behavior%20Dataset.zip"

# Expected output directory
OUTPUT_DIR = "data/raw"

def _download_file(url: str, dest_path: str) -> bool:
    """
    Download a file from a URL to a destination path.
    
    Args:
        url: The URL to download from.
        dest_path: The local path to save the file.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        logger.info(f"Attempting to download from {url}...")
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=30) as response:
            if response.status == 200:
                with open(dest_path, 'wb') as f:
                    f.write(response.read())
                logger.info(f"Successfully downloaded {url} to {dest_path}")
                return True
            else:
                logger.warning(f"Download failed with status {response.status} for {url}")
                return False
    except (URLError, HTTPError, TimeoutError) as e:
        logger.warning(f"Network error downloading {url}: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error downloading {url}: {e}")
        return False

def _extract_zip(zip_path: str, extract_to: str) -> Optional[str]:
    """
    Extract a zip file to a directory and return the path to the extracted CSV.
    
    Args:
        zip_path: Path to the zip file.
        extract_to: Directory to extract to.
        
    Returns:
        Path to the main CSV file inside, or None if extraction failed.
    """
    try:
        os.makedirs(extract_to, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        # Find CSV files
        csv_files = [f for f in os.listdir(extract_to) if f.endswith('.csv')]
        if not csv_files:
            # Check subdirectories
            for root, dirs, files in os.walk(extract_to):
                for f in files:
                    if f.endswith('.csv'):
                        return os.path.join(root, f)
            logger.warning(f"No CSV files found in extracted zip at {zip_path}")
            return None
        
        # Return the first CSV found
        csv_path = os.path.join(extract_to, csv_files[0])
        logger.info(f"Extracted CSV found at: {csv_path}")
        return csv_path
    except Exception as e:
        logger.error(f"Failed to extract zip {zip_path}: {e}")
        return None

def _load_openml_dataset(dataset_id: int) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Attempt to load a dataset from OpenML.
    
    Args:
        dataset_id: The OpenML dataset ID.
        
    Returns:
        Tuple of (DataFrame or None, status_message).
    """
    # OpenML API endpoint for dataset description
    api_url = f"https://www.openml.org/api/v1/json/data/{dataset_id}"
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"dataset_{dataset_id}.zip")
    csv_path = None

    try:
        # First, try to get metadata to check availability
        try:
            with urlopen(api_url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                if 'error' in data:
                    return None, "OpenML dataset not found or API error"
        except Exception:
            return None, "OpenML API unavailable"

        # Try to download the data file (usually available via a specific endpoint)
        # OpenML data download URL pattern
        download_url = f"https://www.openml.org/data/get_csv/{dataset_id}"
        if _download_file(download_url, zip_path):
            csv_path = _extract_zip(zip_path, os.path.join(temp_dir, "extracted"))
            if csv_path:
                df = pd.read_csv(csv_path)
                if df.empty:
                    return None, "Downloaded dataset is empty"
                return df, "success"
        
        return None, "OpenML download failed"
    except Exception as e:
        logger.warning(f"OpenML attempt failed: {e}")
        return None, f"OpenML error: {str(e)}"
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

def _load_uci_dataset(url: str, name: str) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Load a dataset from UCI repository.
    
    Args:
        url: The URL of the zip file.
        name: A friendly name for logging.
        
    Returns:
        Tuple of (DataFrame or None, status_message).
    """
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"{name}.zip")
    csv_path = None

    try:
        if _download_file(url, zip_path):
            csv_path = _extract_zip(zip_path, os.path.join(temp_dir, "extracted"))
            if csv_path:
                df = pd.read_csv(csv_path)
                if df.empty:
                    return None, f"{name} dataset is empty"
                return df, "success"
        return None, f"{name} download failed"
    except Exception as e:
        logger.warning(f"{name} attempt failed: {e}")
        return None, f"{name} error: {str(e)}"
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

def download_dataset() -> Dict[str, Any]:
    """
    Main entry point for dataset acquisition.
    Attempts OpenML first, then falls back to UCI HAR and UCI Shopper.
    
    Returns:
        Dictionary containing:
            - 'data': The loaded DataFrame
            - 'source': The source URL used
            - 'checksum': SHA256 checksum of the file
            - 'status': 'success' or 'failed'
            - 'message': Status message
    """
    pin_random_seed(get_config().RANDOM_SEED)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    result = {
        'data': None,
        'source': None,
        'checksum': None,
        'status': 'failed',
        'message': ''
    }

    # 1. Try OpenML
    logger.info("Attempting to download from OpenML Small Datasets collection...")
    df, status_msg = _load_openml_dataset(OPENML_DATASET_ID)
    
    if df is not None:
        logger.info(f"Successfully loaded dataset from OpenML ({OPENML_DATASET_ID})")
        # Save to raw data
        file_name = f"openml_dataset_{OPENML_DATASET_ID}.csv"
        file_path = os.path.join(OUTPUT_DIR, file_name)
        df.to_csv(file_path, index=False)
        
        checksum = compute_file_checksum(file_path)
        result['data'] = df
        result['source'] = f"https://www.openml.org/d/{OPENML_DATASET_ID}"
        result['checksum'] = checksum
        result['status'] = 'success'
        result['message'] = 'Loaded from OpenML'
        return result

    # 2. Fallback to UCI HAR
    logger.warning("Fallback to UCI: OpenML unavailable or empty")
    df, status_msg = _load_uci_dataset(UCI_HAR_URL, "UCI HAR")
    
    if df is not None:
        logger.info(f"Successfully loaded dataset from UCI HAR")
        file_name = "uci_har_dataset.csv"
        file_path = os.path.join(OUTPUT_DIR, file_name)
        df.to_csv(file_path, index=False)
        
        checksum = compute_file_checksum(file_path)
        result['data'] = df
        result['source'] = UCI_HAR_URL
        result['checksum'] = checksum
        result['status'] = 'success'
        result['message'] = 'Loaded from UCI HAR (Fallback)'
        return result

    # 3. Fallback to UCI Shopper
    logger.warning("Fallback to UCI: UCI HAR unavailable or empty, trying Shopper")
    df, status_msg = _load_uci_dataset(UCI_SHOPPER_URL, "UCI Shopper")
    
    if df is not None:
        logger.info(f"Successfully loaded dataset from UCI Shopper")
        file_name = "uci_shopper_dataset.csv"
        file_path = os.path.join(OUTPUT_DIR, file_name)
        df.to_csv(file_path, index=False)
        
        checksum = compute_file_checksum(file_path)
        result['data'] = df
        result['source'] = UCI_SHOPPER_URL
        result['checksum'] = checksum
        result['status'] = 'success'
        result['message'] = 'Loaded from UCI Shopper (Fallback)'
        return result

    # All sources failed
    result['message'] = f"All sources failed: {status_msg}"
    logger.error("Failed to download dataset from all sources")
    return result

if __name__ == "__main__":
    # Setup logging for standalone execution
    setup_logging("INFO")
    
    logger.info("Starting dataset acquisition...")
    result = download_dataset()
    
    if result['status'] == 'success':
        logger.info(f"Acquisition successful. Source: {result['source']}")
        logger.info(f"Checksum: {result['checksum']}")
        logger.info(f"Dataset shape: {result['data'].shape}")
        logger.info(f"Columns: {list(result['data'].columns)}")
    else:
        logger.error(f"Acquisition failed: {result['message']}")
        exit(1)
