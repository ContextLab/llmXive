import os
import json
import logging
import hashlib
from typing import Optional, Tuple, Dict, Any, List
from urllib.request import urlopen, Request
import pandas as pd
import numpy as np
from utils import compute_file_checksum, setup_logging

logger = logging.getLogger(__name__)

DATASET_URLS = {
    "har": "https://archive.ics.uci.edu/ml/machine-learning-databases/00238/UCI HAR Dataset.zip",
    "shopper": "https://archive.ics.uci.edu/ml/machine-learning-databases/00461/online_shoppers_intention.zip"
}

def download_dataset(dataset_name: str, output_dir: str) -> Optional[str]:
    """
    Download a dataset from a known URL.
    Returns the path to the downloaded file or None on failure.
    """
    url = DATASET_URLS.get(dataset_name)
    if not url:
        logger.error(f"Unknown dataset: {dataset_name}")
        return None
    
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{dataset_name}.zip"
    filepath = os.path.join(output_dir, filename)
    
    logger.info(f"Downloading {dataset_name} from {url}")
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=30) as response:
            with open(filepath, 'wb') as out_file:
                out_file.write(response.read())
        logger.info(f"Downloaded {dataset_name} to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to download {dataset_name}: {e}")
        return None

def load_datasets_from_raw(raw_dir: str) -> Dict[str, pd.DataFrame]:
    """Load all CSV datasets from raw directory."""
    datasets = {}
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw directory not found: {raw_dir}")
        return datasets
    
    for filename in os.listdir(raw_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(raw_dir, filename)
            try:
                df = pd.read_csv(filepath)
                # Clean column names
                df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
                datasets[filename.replace('.csv', '')] = df
                logger.info(f"Loaded dataset: {filename} ({len(df)} rows)")
            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")
    return datasets

def ensure_data_exists(raw_dir: str = "data/raw") -> bool:
    """
    Ensure datasets are available. Download if necessary.
    Returns True if data is available, False otherwise.
    """
    os.makedirs(raw_dir, exist_ok=True)
    
    # Check if any CSV exists
    existing_csvs = [f for f in os.listdir(raw_dir) if f.endswith('.csv')]
    if existing_csvs:
        logger.info(f"Found {len(existing_csvs)} existing datasets")
        return True
    
    # Try to download
    for name in DATASET_URLS.keys():
        logger.info(f"Attempting download for {name}...")
        zip_path = download_dataset(name, raw_dir)
        if zip_path:
            # Extract (simplified: assume CSV is in root or known location)
            # In real implementation, use zipfile
            logger.info(f"Downloaded {name}. In production, extract zip here.")
            # For now, return False as we can't extract without zipfile import
            return False
    
    logger.error("No datasets available and downloads failed.")
    return False

def compute_checksum(filepath: str) -> str:
    """Wrapper for compute_file_checksum."""
    return compute_file_checksum(filepath)

def main():
    """Main entry point for data_loader module."""
    setup_logging("INFO")
    ensure_data_exists()

if __name__ == "__main__":
    main()
