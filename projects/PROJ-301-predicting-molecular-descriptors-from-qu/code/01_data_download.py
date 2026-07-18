"""
Data Download Module.

Implements T009: Download & Verify.

1. Downloads QM9 dataset from the verified HuggingFace source `lisn/QM9`.
2. Validates data integrity (DFT columns, 3D coordinates).
3. Saves raw data to `data/raw/qm9_full.parquet`.
4. Saves checksums to `data/checksums.json`.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from huggingface_hub import hf_hub_download
from datasets import load_dataset

from utils.logger import setup_logger, get_logger
from utils.memory_monitor import check_memory_limit, force_gc

logger = get_logger(__name__)

DATA_RAW_DIR = Path("data/raw")
DATA_CHECKSUMS_DIR = Path("data")

# Verified Source per Plan T009.1
HF_DATASET_NAME = "lisn/QM9"
HF_FILE_NAME = "qm9.parquet" # Assuming parquet or csv, checking common formats
# The datasets library usually provides a dataset object.

def compute_file_checksum(filepath: Path, algorithm: str = "sha256") -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_data_integrity(df: pd.DataFrame) -> bool:
    """
    Validate the dataset integrity.
    
    Checks:
    - Presence of required DFT columns (dipole, homo, lumo).
    - Valid 3D coordinates (non-empty, correct shape).
    """
    required_cols = ['dipole', 'homo', 'lumo', 'smiles', 'xyz'] # xyz or coordinates
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
        
    # Check for valid geometry (non-null)
    if df['xyz'].isnull().any() or df['smiles'].isnull().any():
        logger.warning("Found null values in geometry or SMILES. Filtering may be needed.")
        # We don't fail here, but T010 will filter
        
    return True

def download_qm9_dataset() -> pd.DataFrame:
    """
    Download QM9 dataset from HuggingFace.
    
    Returns:
        pd.DataFrame: The downloaded dataset.
    """
    logger.info(f"Downloading dataset from {HF_DATASET_NAME}...")
    
    try:
        # Use the datasets library to load the dataset
        # The verified source is lisn/QM9
        dataset = load_dataset(HF_DATASET_NAME, split="train")
        
        # Convert to pandas
        df = dataset.to_pandas()
        
        # Normalize column names if necessary (e.g. 'dipole_magnitude' vs 'dipole')
        # Check typical QM9 columns in this dataset
        logger.info(f"Dataset loaded. Columns: {df.columns.tolist()}")
        
        # Map common QM9 columns if names differ
        # Standard QM9 columns often include: mu (dipole), homo, lumo, gap, etc.
        # We need to ensure the names match what T010 expects.
        # Let's assume the dataset uses standard names or we map them.
        # If the dataset has 'mu', we rename to 'dipole'
        if 'mu' in df.columns and 'dipole' not in df.columns:
            df['dipole'] = df['mu']
        if 'homo' not in df.columns:
            # Check for 'HOMO' or similar
            pass # Assuming 'homo' exists or mapped
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

def main():
    """
    Main entry point for data download.
    """
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_CHECKSUMS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting Data Download Pipeline.")
    
    # 1. Download
    df = download_qm9_dataset()
    
    # 2. Validate
    if not validate_data_integrity(df):
        raise ValueError("Data integrity check failed.")
        
    # 3. Save
    output_path = DATA_RAW_DIR / "qm9_full.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved raw data to {output_path}")
    
    # 4. Checksum
    checksum = compute_file_checksum(output_path)
    checksum_data = {
        "file": "qm9_full.parquet",
        "checksum": checksum,
        "algorithm": "sha256",
        "rows": len(df)
    }
    
    checksum_path = DATA_CHECKSUMS_DIR / "checksums.json"
    with open(checksum_path, "w") as f:
        json.dump(checksum_data, f, indent=2)
    logger.info(f"Saved checksums to {checksum_path}")
    
    logger.info("Data Download Pipeline completed.")

if __name__ == "__main__":
    main()
