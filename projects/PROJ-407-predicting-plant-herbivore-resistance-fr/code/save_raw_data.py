"""
Task T014: Save raw downloaded data to data/raw/ with checksum verification.

This script fetches the raw dataset from the verified HuggingFace source,
saves it to data/raw/raw_dataset.csv, and generates a SHA256 checksum file
at data/raw/raw_dataset.csv.sha256.

It depends on the load_raw_dataset function from code/ingest.py.
"""
import os
import sys
import hashlib
import logging
import pandas as pd
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingest import load_raw_dataset
from config import DATA_ROOT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_sha256(filepath):
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    logger.info("Starting raw data ingestion and saving (Task T014)...")
    
    # Define output paths
    data_raw_dir = Path(DATA_ROOT) / "raw"
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    
    raw_csv_path = data_raw_dir / "raw_dataset.csv"
    checksum_path = data_raw_dir / "raw_dataset.csv.sha256"
    
    # Load raw dataset using the existing ingest module
    logger.info("Loading raw dataset from HuggingFace...")
    try:
        raw_dataset = load_raw_dataset()
        logger.info(f"Successfully loaded raw dataset with {len(raw_dataset)} rows.")
    except Exception as e:
        logger.error(f"Failed to load raw dataset: {e}")
        raise
    
    # Convert to DataFrame and save to CSV
    logger.info(f"Saving raw dataset to {raw_csv_path}...")
    df = raw_dataset.to_pandas()
    df.to_csv(raw_csv_path, index=False)
    logger.info(f"Saved {len(df)} rows to {raw_csv_path}")
    
    # Compute and save checksum
    logger.info(f"Computing SHA256 checksum for {raw_csv_path}...")
    checksum = compute_sha256(raw_csv_path)
    
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  raw_dataset.csv\n")
    
    logger.info(f"Checksum saved to {checksum_path}: {checksum}")
    logger.info("Task T014 completed successfully.")

if __name__ == "__main__":
    main()
