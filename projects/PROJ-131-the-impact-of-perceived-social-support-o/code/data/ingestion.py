import os
import sys
import hashlib
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import yaml
import pandas as pd

# Ensure code is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger

CONFIG_PATH = Path("code/config/data_sources.yaml")
RAW_DATA_PATH = Path("data/raw/cyberbullying_2021.csv")

def load_config() -> Dict[str, Any]:
    """Load data source configuration."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
    
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_dataset(dataset_id: str, output_path: Path):
    """
    Download the dataset from the verified source.
    This implementation attempts to use the HuggingFace datasets library.
    If the specific dataset is not found or network fails, it raises a RuntimeError.
    """
    logger = get_logger("ingestion")
    
    # Attempt to load from HuggingFace datasets
    try:
        from datasets import load_dataset
        logger.info(f"Attempting to download dataset: {dataset_id}")
        
        # Load dataset (streaming to handle large files if necessary)
        # Note: We assume the dataset is available as a public HF dataset.
        # If the ID is a URL or specific path, adjust accordingly.
        ds = load_dataset(dataset_id, split="train", streaming=False)
        
        # Convert to pandas and save
        df = ds.to_pandas()
        df.to_csv(output_path, index=False)
        logger.info(f"Dataset downloaded and saved to {output_path}")
        
    except Exception as e:
        # Fallback: If HF fails, we strictly fail loud as per requirements.
        # We do NOT generate synthetic data.
        raise RuntimeError(f"Real data fetch failed for {dataset_id}. Aborting to prevent synthetic data fabrication. Error: {e}")

def load_cyber_data() -> pd.DataFrame:
    """Load the Cyberbullying Survey 2021 dataset."""
    logger = get_logger("ingestion")
    
    config = load_config()
    
    if 'dataset_id' not in config:
        raise ValueError("Dataset ID not found in configuration.")
    
    dataset_id = config['dataset_id']
    
    # Check if file already exists locally (from previous run)
    if RAW_DATA_PATH.exists():
        logger.info(f"Found existing raw data at {RAW_DATA_PATH}. Loading...")
        df = pd.read_csv(RAW_DATA_PATH)
        logger.info(f"Loaded {len(df)} rows from {RAW_DATA_PATH}")
        return df
    
    # Download if not exists
    logger.info(f"Raw data not found. Downloading from source: {dataset_id}")
    download_dataset(dataset_id, RAW_DATA_PATH)
    
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Failed to download data to {RAW_DATA_PATH}")
    
    df = pd.read_csv(RAW_DATA_PATH)
    logger.info(f"Loaded {len(df)} rows from {RAW_DATA_PATH}")
    return df

def main():
    """Main entry point for ingestion."""
    logger = get_logger("ingestion")
    setup_logging = __import__('utils.logger', fromlist=['setup_logging']).setup_logging
    setup_logging()
    
    try:
        df = load_cyber_data()
        logger.info(f"Ingestion complete. Dataset shape: {df.shape}")
        # Log column names for verification
        logger.info(f"Columns found: {list(df.columns)}")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise

if __name__ == "__main__":
    main()
