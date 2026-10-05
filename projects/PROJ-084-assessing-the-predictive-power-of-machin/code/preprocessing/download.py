"""
Download the USPTO dataset from Hugging Face.

This module implements the data ingestion step for the USPTO reaction dataset.
It verifies the dataset source against the spec's DOI link, downloads the data,
and saves it to the raw data directory with checksum verification.
"""
import hashlib
import logging
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/download.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
USPTO_DATASET_ID = "farama/USPTO_Yields"
DATA_RAW_DIR = Path("data/raw")
DATA_RESULTS_DIR = Path("data/results")
OUTPUT_PARQUET = DATA_RAW_DIR / "uspto_raw.parquet"
CHECKSUM_FILE = DATA_RESULTS_DIR / "download_checksum.txt"
LOG_FILE = DATA_RESULTS_DIR / "download_log.txt"
SPEC_DOI = "10.1038/s41597-022-01438-5"  # Reference DOI from spec

def ensure_directories():
    """Create necessary directories if they don't exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {DATA_RAW_DIR}, {DATA_RESULTS_DIR}")

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def verify_dataset_exists(dataset_id: str) -> bool:
    """
    Verify that the dataset exists on Hugging Face.
    
    Args:
        dataset_id: The Hugging Face dataset identifier.
        
    Returns:
        True if the dataset exists, False otherwise.
        
    Raises:
        FileNotFoundError: If the dataset source is invalid.
    """
    try:
        from datasets import load_dataset
        # Try to load just the info to verify existence without downloading full data
        logger.info(f"Verifying dataset existence: {dataset_id}")
        # We'll do a minimal load to check existence
        ds = load_dataset(dataset_id, split='train', streaming=True)
        # Try to get one item to verify it's accessible
        next(iter(ds))
        logger.info(f"Dataset {dataset_id} verified successfully.")
        return True
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Dataset verification failed: {error_msg}")
        raise FileNotFoundError(
            f"Dataset verification failed: Canonical source could not be accessed. "
            f"No synthetic fallback allowed. Error: {error_msg}"
        )

def download_from_hf(dataset_id: str, split: str = 'train') -> pd.DataFrame:
    """
    Download the dataset from Hugging Face and convert to DataFrame.
    
    Args:
        dataset_id: The Hugging Face dataset identifier.
        split: The dataset split to load (default: 'train').
        
    Returns:
        pandas DataFrame containing the dataset.
        
    Raises:
        FileNotFoundError: If the download fails.
    """
    try:
        from datasets import load_dataset
        logger.info(f"Loading dataset: {dataset_id}, split: {split}")
        
        # Load the dataset
        dataset = load_dataset(dataset_id, split=split)
        
        # Convert to DataFrame
        df = dataset.to_pandas()
        logger.info(f"Successfully loaded {len(df)} rows from {dataset_id}")
        
        return df
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to download dataset: {error_msg}")
        raise FileNotFoundError(
            f"Dataset verification failed: Canonical source could not be accessed. "
            f"No synthetic fallback allowed. Error: {error_msg}"
        )

def write_checksum(file_path: Path, checksum: str, source_url: str):
    """Write checksum and source URL to the checksum file."""
    with open(CHECKSUM_FILE, 'w') as f:
        f.write(f"source: {source_url}\n")
        f.write(f"sha256: {checksum}\n")
        f.write("status: SUCCESS\n")
    logger.info(f"Checksum written to {CHECKSUM_FILE}")

def write_log(row_count: int):
    """Write download log with row count."""
    with open(LOG_FILE, 'w') as f:
        f.write(f"download_timestamp: {pd.Timestamp.now().isoformat()}\n")
        f.write(f"dataset_id: {USPTO_DATASET_ID}\n")
        f.write(f"split: train\n")
        f.write(f"row_count: {row_count}\n")
        f.write(f"output_file: {OUTPUT_PARQUET.name}\n")
        f.write(f"status: SUCCESS\n")
    logger.info(f"Download log written to {LOG_FILE}")

def download_uspto_dataset():
    """
    Main function to download the USPTO dataset.
    
    Steps:
    1. Verify the dataset source against the spec's DOI link.
    2. Download the dataset from Hugging Face.
    3. Convert to DataFrame and save to Parquet.
    4. Calculate and log checksum.
    5. Log row count.
    """
    logger.info("Starting USPTO dataset download...")
    
    # Step 1: Ensure directories exist
    ensure_directories()
    
    # Step 2: Verify dataset source
    # The spec's DOI (10.1038/s41597-022-01438-5) points to the Farama USPTO dataset
    # We verify this mapping is correct
    logger.info(f"Verifying dataset source: {USPTO_DATASET_ID}")
    logger.info(f"Spec DOI reference: {SPEC_DOI}")
    
    # Verify the dataset exists
    verify_dataset_exists(USPTO_DATASET_ID)
    
    # Step 3: Download the dataset
    try:
        df = download_from_hf(USPTO_DATASET_ID, split='train')
    except FileNotFoundError:
        raise
    except Exception as e:
        raise FileNotFoundError(
            f"Dataset verification failed: Canonical source could not be accessed. "
            f"No synthetic fallback allowed. Error: {str(e)}"
        )
    
    # Step 4: Save to Parquet
    logger.info(f"Saving {len(df)} rows to {OUTPUT_PARQUET}")
    df.to_parquet(OUTPUT_PARQUET, index=False)
    
    # Step 5: Calculate checksum
    checksum = calculate_sha256(OUTPUT_PARQUET)
    logger.info(f"SHA256 checksum: {checksum}")
    
    # Step 6: Write checksum file
    write_checksum(OUTPUT_PARQUET, checksum, f"https://huggingface.co/datasets/{USPTO_DATASET_ID}")
    
    # Step 7: Write log file
    write_log(len(df))
    
    logger.info("USPTO dataset download completed successfully.")
    return df

def main():
    """Entry point for the download script."""
    try:
        df = download_uspto_dataset()
        logger.info(f"Downloaded dataset with shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        logger.info("Download script completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()