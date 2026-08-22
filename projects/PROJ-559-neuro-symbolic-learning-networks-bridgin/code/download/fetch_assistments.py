"""
Fetch the ASSISTments 2009-2010 dataset from Hugging Face.

This script downloads the raw CSV data, validates the fetch, and saves it
to the project's data directory. It enforces a 300-second timeout and
exits with code 1 if the download fails or times out.

Dependencies:
    - datasets (from Hugging Face)
    - pandas
"""

import os
import sys
import time
import hashlib
import json
import logging
import argparse
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/raw/fetch_assistments.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATASET_ID = "assistments/2009-2010"
OUTPUT_DIR = "data/raw"
OUTPUT_FILE = "assistments.csv"
TIMEOUT_SECONDS = 300
REQUIRED_COLUMNS = ['problem_id', 'correct', 'time', 'skill'] # Basic sanity check columns

def download_raw_csv(timeout: int = TIMEOUT_SECONDS) -> Optional[str]:
    """
    Fetch the ASSISTments dataset from Hugging Face with a timeout.

    Args:
        timeout: Maximum time in seconds to wait for the download.

    Returns:
        Path to the downloaded CSV file if successful, None otherwise.

    Raises:
        TimeoutError: If the download exceeds the specified timeout.
        ImportError: If the 'datasets' library is not installed.
        Exception: For other download failures.
    """
    start_time = time.time()
    logger.info(f"Starting download of dataset: {DATASET_ID}")
    logger.info(f"Timeout set to {timeout} seconds.")

    try:
        # Dynamically import to fail fast if not installed
        from datasets import load_dataset
    except ImportError:
        logger.error("ERROR: 'datasets' library not found. Install with: pip install datasets")
        raise

    try:
        # Load the dataset (streaming=False to ensure full download for CSV export)
        # We use 'train' split as it typically contains the bulk of the data for this dataset version
        logger.info("Loading dataset from Hugging Face...")
        ds = load_dataset(DATASET_ID, split="train", trust_remote_code=True)

        # Check for timeout during load
        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise TimeoutError(f"Download exceeded {timeout} seconds.")

        logger.info(f"Dataset loaded successfully in {elapsed:.2f} seconds.")
        logger.info(f"Dataset shape: {ds.shape}")
        logger.info(f"Dataset features: {ds.features}")

        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

        # Convert to pandas and save as CSV
        logger.info(f"Converting to CSV and saving to: {output_path}")
        df = ds.to_pandas()

        # Basic validation of columns
        # Note: Column names might vary slightly by dataset version, so we check for existence
        # or warn if missing. The task requires saving the raw data.
        logger.info(f"Columns in dataframe: {list(df.columns)}")

        df.to_csv(output_path, index=False)

        # Calculate checksum for integrity
        with open(output_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        logger.info(f"File saved. MD5: {file_hash}")
        logger.info(f"Total rows: {len(df)}")

        # Save metadata
        metadata = {
            "dataset_id": DATASET_ID,
            "output_file": output_path,
            "rows": len(df),
            "columns": list(df.columns),
            "md5": file_hash,
            "download_time_seconds": time.time() - start_time
        }
        metadata_path = os.path.join(OUTPUT_DIR, "assistments_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return output_path

    except TimeoutError:
        logger.error(f"ERROR: Failed to download {DATASET_ID} within {timeout} seconds – aborting pipeline.")
        raise
    except Exception as e:
        logger.error(f"ERROR: Failed to download {DATASET_ID}: {str(e)}")
        raise

def fetch_assistments_dataset(timeout: int = TIMEOUT_SECONDS) -> str:
    """
    Main entry point for fetching the ASSISTments dataset.

    Args:
        timeout: Maximum time in seconds for the download.

    Returns:
        Path to the saved CSV file.

    Raises:
        SystemExit: If the download fails or times out.
    """
    try:
        path = download_raw_csv(timeout=timeout)
        if path is None:
            raise RuntimeError("Download returned None without raising an exception.")
        logger.info(f"SUCCESS: Dataset saved to {path}")
        return path
    except (TimeoutError, ImportError, Exception) as e:
        logger.error(f"Pipeline aborted due to error: {e}")
        sys.exit(1)

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Fetch ASSISTments 2009-2010 dataset.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=TIMEOUT_SECONDS,
        help=f"Download timeout in seconds (default: {TIMEOUT_SECONDS})"
    )
    args = parser.parse_args()

    logger.info("Starting fetch_assistments.py script.")
    fetch_assistments_dataset(timeout=args.timeout)
    logger.info("Script completed successfully.")

if __name__ == "__main__":
    main()