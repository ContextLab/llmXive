import os
import sys
import logging
import time
import json
import hashlib
import argparse
from pathlib import Path
from typing import Optional

# Attempt to import datasets; if missing, the script will fail loudly as per constraints
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' package is required. Install with: pip install datasets")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = "oqmd/formation-energy"
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "oqmd.parquet"
CHECKSUM_FILE = Path("data/checksums.json")
MAX_RETRIES = 3
BASE_DELAY = 2.0  # seconds

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def download_oqmd_dataset(retries: int = MAX_RETRIES) -> bool:
    """
    Fetch the OQMD Formation Energy dataset via HuggingFace with retry logic.
    Materializes the dataset to parquet and records the checksum.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    attempt = 0
    last_exception = None

    while attempt < retries:
        try:
            logger.info(f"Attempt {attempt + 1}/{retries}: Loading dataset '{DATASET_NAME}'...")
            
            # Load dataset (streaming=False as per requirement)
            dataset = load_dataset(DATASET_NAME, streaming=False)
            
            logger.info("Dataset loaded successfully. Materializing to Parquet...")
            
            # Explicitly call to_parquet to materialize
            # The dataset object from load_dataset usually has a 'train' split or is a dict-like structure
            # We assume the dataset has a primary split (usually 'train' or the dataset itself if single)
            if isinstance(dataset, dict):
                # If it's a dict of splits, we usually want the main one or all
                # For OQMD formation energy, it's typically a single split or 'train'
                split_key = 'train' if 'train' in dataset else list(dataset.keys())[0]
                dataset_to_save = dataset[split_key]
            else:
                dataset_to_save = dataset

            # Save to parquet
            dataset_to_save.to_parquet(str(OUTPUT_FILE))
            
            if not OUTPUT_FILE.exists():
                raise FileNotFoundError(f"Failed to create output file: {OUTPUT_FILE}")

            logger.info(f"Dataset saved to {OUTPUT_FILE}")

            # Calculate checksum
            logger.info("Calculating SHA-256 checksum...")
            checksum = calculate_sha256(OUTPUT_FILE)
            
            # Record checksum
            checksum_data = {
                "filename": "oqmd.parquet",
                "sha256": checksum
            }
            
            # Ensure data directory exists for checksum file
            CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            with open(CHECKSUM_FILE, 'w') as f:
                json.dump(checksum_data, f, indent=2)
            
            logger.info(f"Checksum recorded in {CHECKSUM_FILE}: {checksum}")
            return True

        except Exception as e:
            last_exception = e
            attempt += 1
            if attempt < retries:
                delay = BASE_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"All {retries} attempts failed. Last error: {e}")
    
    # If we exit the loop, all retries failed
    raise RuntimeError(f"Failed to download dataset after {retries} attempts. Last error: {last_exception}")

def validate_structural_descriptors(dataset_path: Path) -> None:
    """
    Placeholder for T005b: Validates structural descriptors.
    This function is called by subsequent tasks but not fully implemented here.
    """
    pass

def extract_structural_features(dataset_path: Path) -> None:
    """
    Placeholder for T005c: Extracts structural features.
    """
    pass

def update_validation_report() -> None:
    """
    Placeholder for T005d: Updates validation report.
    """
    pass

def main():
    """Main entry point for the download script."""
    parser = argparse.ArgumentParser(description="Download OQMD Formation Energy dataset")
    parser.add_argument("--retries", type=int, default=MAX_RETRIES, help="Number of retry attempts")
    args = parser.parse_args()

    try:
        success = download_oqmd_dataset(retries=args.retries)
        if success:
            logger.info("Download and verification completed successfully.")
            sys.exit(0)
        else:
            logger.error("Download failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
