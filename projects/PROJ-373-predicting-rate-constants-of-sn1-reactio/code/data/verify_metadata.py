"""
T011a: Verify Metadata for SN1 Dataset Ingestion.

Performs an atomic pre-ingestion check for required columns ('substrate_class', 'temperature', 'solvent')
on the HuggingFace datasets.
- If columns are missing: Writes 'ABORTED' to pipeline_status, logs fatal error with reason 'missing_metadata', exits 1.
- If columns exist: Writes 'OK' to pipeline_status.
- No synthetic fallbacks.
- No re-fetching loops (single pass with immediate termination on failure).
- Handles network errors by failing immediately with exit code 1.
"""
import sys
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

# Ensure output directories exist before any file operations
ensure_dirs()
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
PIPELINE_STATUS_FILE = PROCESSED_DIR / ".pipeline_status"
CLEAN_LOG_FILE = PROCESSED_DIR / "clean.log"

def log_fatal_error(message: str, logger: logging.Logger):
    """Writes a fatal error entry to the clean log."""
    logger.error(f"FATAL: {message}")
    # Append to clean.log with timestamp-like prefix for clarity
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
        # We only need the features info to check columns
        dataset = load_dataset(dataset_name, split='train', streaming=True, revision='main', trust_remote_code=True)
        
        # Access column_names immediately to trigger the metadata fetch
        # This does not download the data rows, just the schema info
        columns = list(dataset.column_names)
        return columns
    except Exception as e:
        raise RuntimeError(f"Failed to fetch metadata for dataset '{dataset_name}': {e}")

def check_columns_exist(columns: List[str], required: List[str]) -> bool:
    """Checks if all required columns are present in the dataset columns."""
    return all(col in columns for col in required)

def main():
    logger = get_logger("verify_metadata")
    logger.info("Starting metadata verification for SN1 datasets.")

    # Ensure directories exist (redundant but safe)
    ensure_dirs()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    all_datasets_valid = True

    for dataset_name in DATASET_NAMES:
        logger.info(f"Checking dataset: {dataset_name}")
        metadata = None

        try:
            logger.info(f"Fetching metadata for {dataset_name}...")
            metadata = fetch_dataset_metadata(dataset_name)
        except RuntimeError as e:
            # Network error or fetch failure: Immediate termination
            log_fatal_error(f"Network or fetch error for {dataset_name}: {e}", logger)
            write_pipeline_status("ABORTED")
            sys.exit(1)
        except Exception as e:
            # Unexpected error: Immediate termination
            log_fatal_error(f"Unexpected error checking dataset {dataset_name}: {e}", logger)
            write_pipeline_status("ABORTED")
            sys.exit(1)

        if metadata is None or len(metadata) == 0:
            log_fatal_error(f"Metadata for {dataset_name} is empty or None.", logger)
            write_pipeline_status("ABORTED")
            sys.exit(1)

        logger.info(f"Retrieved columns for {dataset_name}: {metadata}")

        if not check_columns_exist(metadata, REQUIRED_COLUMNS):
            missing = [col for col in REQUIRED_COLUMNS if col not in metadata]
            msg = f"Dataset '{dataset_name}' is missing required columns: {missing}. Reason: 'missing_metadata'. Pipeline ABORTED."
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