import os
import json
import logging
import hashlib
from typing import Optional, Tuple, Dict, Any, List
from urllib.request import urlopen, Request
import pandas as pd
import tempfile
import zipfile
import io

logger = logging.getLogger(__name__)

def compute_checksum(data: bytes) -> str:
    """Compute SHA256 checksum of raw bytes."""
    return hashlib.sha256(data).hexdigest()

def download_dataset(url: str, output_dir: str, filename: str) -> Tuple[bool, str]:
    """
    Download a dataset from a URL and save it to output_dir.
    Returns (success, message).
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    if os.path.exists(output_path):
        logger.info(f"Dataset already exists: {output_path}")
        return True, f"Already exists: {output_path}"

    try:
        logger.info(f"Downloading {url}...")
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=30) as response:
            data = response.read()
        
        # Check if it's a zip file
        if filename.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(data)) as zip_ref:
                # Extract first CSV found or specific file
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if csv_files:
                    # Assume the first CSV is the main data
                    main_csv = csv_files[0]
                    with zip_ref.open(main_csv) as csv_file:
                        content = csv_file.read()
                        with open(output_path, 'wb') as f:
                            f.write(content)
                    logger.info(f"Extracted {main_csv} to {output_path}")
                else:
                    logger.error("No CSV found in zip file.")
                    return False, "No CSV in zip"
        else:
            with open(output_path, 'wb') as f:
                f.write(data)
        
        logger.info(f"Downloaded and saved: {output_path}")
        return True, output_path
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False, str(e)

def load_datasets_from_raw(raw_dir: str) -> List[Tuple[str, pd.DataFrame]]:
    """
    Load all CSV files from raw_dir.
    """
    datasets = []
    if not os.path.exists(raw_dir):
        return datasets
    
    for f in os.listdir(raw_dir):
        if f.endswith('.csv'):
            path = os.path.join(raw_dir, f)
            try:
                df = pd.read_csv(path)
                datasets.append((f, df))
            except Exception as e:
                logger.error(f"Failed to load {f}: {e}")
    return datasets

# Default datasets for T011/T012 if raw dir is empty
# UCI HAR (Human Activity Recognition) - small subset
UCI_HAR_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00240/UCI%20HAR%20Dataset.zip"

def ensure_data_exists(raw_dir: str) -> bool:
    """
    Ensure data exists in raw_dir. If not, attempt to download.
    """
    if os.listdir(raw_dir):
        return True
    
    logger.info("Raw directory empty. Downloading UCI HAR dataset...")
    success, msg = download_dataset(UCI_HAR_URL, raw_dir, "UCI_HAR.zip")
    if success:
        return True
    logger.error(f"Failed to download data: {msg}")
    return False
