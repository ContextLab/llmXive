import hashlib
import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from datasets import load_dataset

# Ensure we can find config if needed
try:
    from config import ensure_dirs
except ImportError:
    # Fallback for direct execution context if config is not in sys.path
    def ensure_dirs():
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        Path("data/results").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
HF_DATASET_ID = "farside/uspto-yields"
RAW_DATA_DIR = Path("data/raw")
RESULTS_DIR = Path("data/results")
OUTPUT_FILE = RAW_DATA_DIR / "uspto_raw.parquet"
CHECKSUM_FILE = RESULTS_DIR / "download_checksum.txt"
MEMORY_LIMIT_GB = 7.0

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    logger.info(f"Calculating SHA256 for {file_path}...")
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def download_from_hf(dataset_id: str, output_path: Path) -> Optional[str]:
    """
    Download dataset from HuggingFace Hub.
    Returns the source string if successful, None otherwise.
    Strictly adheres to the requirement: NO synthetic fallback.
    """
    try:
        logger.info(f"Attempting to download dataset '{dataset_id}' from HuggingFace...")
        
        # Step 1: Verify dataset ID exists by loading info
        logger.info("Verifying dataset existence via streaming info load...")
        try:
            ds_stream = load_dataset(dataset_id, split="train", streaming=True)
            info = ds_stream.info
            if info is None:
                raise ValueError("Dataset info is None")
            logger.info(f"Dataset verified. Description: {info.description[:100] if info.description else 'N/A'}...")
        except Exception as verify_err:
            raise FileNotFoundError(f"Dataset verification failed: {verify_err}") from verify_err

        # Step 2: Fetch data
        logger.info("Fetching full dataset (non-streaming) to memory...")
        try:
            dataset = load_dataset(dataset_id, split="train", streaming=False)
        except Exception as load_err:
            # If 'train' split fails, try loading without split to see available splits
            logger.warning(f"Split 'train' not found or failed: {load_err}. Attempting default load.")
            full_dataset = load_dataset(dataset_id, streaming=False)
            if isinstance(full_dataset, dict):
                if "train" in full_dataset:
                    dataset = full_dataset["train"]
                else:
                    # Fallback to first available split if 'train' is missing
                    first_key = next(iter(full_dataset))
                    logger.warning(f"Using split '{first_key}' as 'train' was missing.")
                    dataset = full_dataset[first_key]
            else:
                dataset = full_dataset

        logger.info(f"Dataset loaded. Columns: {dataset.column_names}")
        logger.info(f"Dataset size: {len(dataset)} rows")

        # Convert to DataFrame
        df = dataset.to_pandas()
        
        # Verify memory usage
        mem_usage_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        if mem_usage_mb > (MEMORY_LIMIT_GB * 1024):
            logger.warning(f"Dataset size ({mem_usage_mb:.2f} MB) exceeds recommended limit ({MEMORY_LIMIT_GB} GB). Proceeding...")
        
        # Save to Parquet
        logger.info(f"Saving to {output_path}...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        
        logger.info(f"Successfully saved {output_path}")
        return dataset_id
        
    except Exception as e:
        logger.error(f"Failed to download from HuggingFace: {e}")
        return None

def write_checksum(source: str, checksum: str, file_path: Path) -> None:
    """Write source and checksum to the checksum file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        f.write(f"Source: {source}\n")
        f.write(f"Checksum: {checksum}\n")
    logger.info(f"Wrote checksum to {file_path}")

def download_uspto_dataset() -> None:
    """
    Main orchestration function to download the USPTO dataset.
    1. Verifies dataset exists.
    2. Attempts download from HuggingFace.
    3. If that fails, raises FileNotFoundError.
    4. On success, calculates checksum and writes to data/results/download_checksum.txt.
    """
    source = None
    
    # Try Primary Source
    source = download_from_hf(HF_DATASET_ID, OUTPUT_FILE)
    
    # Per task requirements: DO NOT implement fallback mechanisms.
    # If primary fails, we must fail loudly.
    if source is None:
        error_msg = f"Failed to download dataset from {HF_DATASET_ID}. No fallback allowed."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Verify output file exists
    if not OUTPUT_FILE.exists():
        error_msg = f"Download completed but output file {OUTPUT_FILE} not found."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Calculate and write checksum
    checksum = calculate_sha256(OUTPUT_FILE)
    write_checksum(source, checksum, CHECKSUM_FILE)
    
    logger.info(f"Download complete. Source: {source}, Checksum: {checksum}")

def main():
    """Entry point for the download script."""
    try:
        ensure_dirs()
        download_uspto_dataset()
        logger.info("T019 Download task completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Task failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()