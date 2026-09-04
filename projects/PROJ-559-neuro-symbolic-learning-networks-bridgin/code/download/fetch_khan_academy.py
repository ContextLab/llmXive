"""
Fetch the Khan Academy Math dataset from Hugging Face.

This script downloads the raw CSV data, validates the fetch, and saves it
to the project's data directory. It enforces a 300-second timeout and
exits with code 1 if the download fails or times out.
It uses streaming=True to handle large datasets efficiently.

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
import threading
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/raw/fetch_khan_academy.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATASET_ID = "khan_academy/math"
OUTPUT_DIR = "data/raw"
OUTPUT_FILE = "khan_academy.csv"
TIMEOUT_SECONDS = 300
CHECKSUM_FILE = "khan_academy.csv.md5"

class TimeoutError(Exception):
    """Custom timeout error to distinguish from other exceptions."""
    pass

def download_raw_csv(timeout: int = TIMEOUT_SECONDS) -> Optional[str]:
    """
    Fetch the Khan Academy dataset from Hugging Face with a timeout.

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

    # Import inside function to ensure environment is ready
    try:
        from datasets import load_dataset
        import pandas as pd
    except ImportError as e:
        raise ImportError(f"Required library not found. Please install dependencies: {e}")

    result = [None]
    error = [None]

    def load_data():
        try:
            logger.info("Loading dataset from Hugging Face with streaming=True...")
            # Use streaming=True to handle large datasets efficiently
            # Note: Khan Academy dataset structure might vary; we attempt to load 'train' split
            # If the dataset has a different structure, we adapt by iterating over the dataset
            ds = load_dataset(DATASET_ID, split="train", streaming=True, trust_remote_code=True)
            
            logger.info("Converting streaming dataset to CSV...")
            rows = []
            batch_size = 1000
            count = 0
            
            for item in ds:
                # Check timeout periodically during iteration
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    raise TimeoutError(f"Download exceeded {timeout} seconds.")
                
                rows.append(item)
                count += 1
                if count % batch_size == 0:
                    logger.info(f"Processed {count} rows...")
            
            df = pd.DataFrame(rows)
            logger.info(f"Dataset loaded successfully in {time.time() - start_time:.2f} seconds.")
            logger.info(f"Dataset shape: {df.shape}")
            logger.info(f"Columns: {list(df.columns)}")

            # Ensure output directory exists
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

            logger.info(f"Saving to CSV: {output_path}")
            df.to_csv(output_path, index=False)

            # Calculate checksum
            with open(output_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            # Save checksum file
            checksum_path = os.path.join(OUTPUT_DIR, CHECKSUM_FILE)
            with open(checksum_path, 'w') as f:
                f.write(f"{file_hash}  {OUTPUT_FILE}\n")

            logger.info(f"File saved. MD5: {file_hash}")
            logger.info(f"Total rows: {len(df)}")
            result[0] = output_path

        except Exception as e:
            error[0] = e

    thread = threading.Thread(target=load_data)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        raise TimeoutError(f"Download exceeded {timeout} seconds.")
    
    if error[0] is not None:
        raise error[0]
    
    return result[0]

def fetch_khan_academy_dataset(timeout: int = TIMEOUT_SECONDS) -> str:
    """
    Main entry point for fetching the Khan Academy dataset.

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
    except TimeoutError:
        logger.error(f"ERROR: Failed to download {DATASET_ID} within {timeout} seconds – aborting pipeline.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"ERROR: Failed to download {DATASET_ID}: {str(e)}")
        sys.exit(1)

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Fetch Khan Academy Math dataset.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=TIMEOUT_SECONDS,
        help=f"Download timeout in seconds (default: {TIMEOUT_SECONDS})"
    )
    args = parser.parse_args()

    logger.info("Starting fetch_khan_academy.py script.")
    fetch_khan_academy_dataset(timeout=args.timeout)
    logger.info("Script completed successfully.")

if __name__ == "__main__":
    main()