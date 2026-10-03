"""
T011a: Verify Metadata for SN1 Dataset Ingestion.

Performs an atomic pre-ingestion check for required columns ('substrate_class', 'temperature', 'solvent')
on the HuggingFace datasets.
- If columns are missing: Writes 'ABORTED' to pipeline_status, logs fatal error, exits 1.
- If columns exist: Writes 'OK' to pipeline_status.
- No synthetic fallbacks.
- No re-fetching.
"""
import sys
import time
import logging
from pathlib import Path
from typing import List

# Import from existing project modules
from config import DataConfig, ensure_dirs
from utils.logger import get_logger

# Constants
REQUIRED_COLUMNS = ['substrate_class', 'temperature', 'solvent']
DATASET_NAMES = [
    "DTS-SN1-15-01-2024",
    "SN18-All-20240204"
]
MAX_RETRIES = 3
BASE_DELAY = 2.0  # seconds

# Ensure output directories exist
ensure_dirs()
PROCESSED_DIR = Path("data/processed")
PIPELINE_STATUS_FILE = PROCESSED_DIR / ".pipeline_status"
CLEAN_LOG_FILE = PROCESSED_DIR / "clean.log"

def log_fatal_error(message: str, logger: logging.Logger):
    """Writes a fatal error entry to the clean log."""
    logger.error(f"FATAL: {message}")
    with open(CLEAN_LOG_FILE, 'a') as f:
        f.write(f"CRITICAL: {message}\n")

def write_pipeline_status(status: str):
    """Writes the status to the pipeline status file."""
    with open(PIPELINE_STATUS_FILE, 'w') as f:
        f.write(status)

def fetch_dataset_metadata(dataset_name: str) -> List[str]:
    """
    Fetches the column names (schema) from the HuggingFace dataset using streaming.
    Returns a list of column names.
    Raises an exception if the dataset cannot be accessed.
    """
    try:
        from datasets import load_dataset
        # Use streaming=True to avoid downloading the full dataset just for metadata
        dataset = load_dataset(dataset_name, split='train', streaming=True, revision='main')
        return list(dataset.column_names)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch metadata for dataset '{dataset_name}': {e}")

def check_columns_exist(columns: List[str], required: List[str]) -> bool:
    """Checks if all required columns are present in the dataset columns."""
    return all(col in columns for col in required)

def main():
    logger = get_logger("verify_metadata")
    logger.info("Starting metadata verification for SN1 datasets.")

    # Ensure directories exist
    ensure_dirs()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    all_datasets_valid = True

    for dataset_name in DATASET_NAMES:
        logger.info(f"Checking dataset: {dataset_name}")
        attempt = 0
        success = False
        metadata = None

        while attempt < MAX_RETRIES and not success:
            try:
                logger.info(f"Attempt {attempt + 1}/{MAX_RETRIES} to fetch metadata for {dataset_name}...")
                metadata = fetch_dataset_metadata(dataset_name)
                success = True
            except RuntimeError as e:
                attempt += 1
                delay = BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(f"Error fetching metadata: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            except Exception as e:
                # Unexpected error, fail immediately
                log_fatal_error(f"Unexpected error checking dataset {dataset_name}: {e}", logger)
                write_pipeline_status("ABORTED")
                sys.exit(1)

        if not success:
            log_fatal_error(f"Failed to fetch metadata for {dataset_name} after {MAX_RETRIES} retries.", logger)
            write_pipeline_status("ABORTED")
            sys.exit(1)

        logger.info(f"Retrieved columns for {dataset_name}: {metadata}")

        if not check_columns_exist(metadata, REQUIRED_COLUMNS):
            missing = [col for col in REQUIRED_COLUMNS if col not in metadata]
            msg = f"Dataset '{dataset_name}' is missing required columns: {missing}. Pipeline ABORTED."
            log_fatal_error(msg, logger)
            write_pipeline_status("ABORTED")
            sys.exit(1)

        logger.info(f"Dataset '{dataset_name}' passed metadata check.")

    # If we reach here, all datasets are valid
    write_pipeline_status("OK")
    logger.info("Metadata verification complete. Pipeline status set to OK.")
    sys.exit(0)

if __name__ == "__main__":
    main()