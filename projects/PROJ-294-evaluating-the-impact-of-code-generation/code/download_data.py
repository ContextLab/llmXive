import os
import sys
import json
import time
import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime

# Ensure we can import from the project root if run as a script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from utils import compute_sha256, setup_logging, get_logger, set_task_id, get_task_id
except ImportError:
    # Fallback if utils is not available (should not happen in correct setup)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("download_data")
    def set_task_id(x): pass
    def get_task_id(): return "T010"
    def setup_logging(*args, **kwargs): return logger
    def get_logger(): return logger

TASK_ID = "T010"
set_task_id(TASK_ID)
logger = setup_logging(task_id=TASK_ID)

# Constants
DATASET_NAME = "openai/openai_humaneval"
DATASET_REVISION = "v1.0.0"  # Specific revision for deterministic versioning
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
METADATA_FILE = os.path.join(PROJECT_ROOT, "data", "metadata.yaml")
PARQUET_FILENAME = "humaneval.parquet"
PARQUET_PATH = os.path.join(RAW_DATA_DIR, PARQUET_FILENAME)

# Exponential backoff constants
MAX_RETRIES = 5
INITIAL_DELAY = 2  # seconds
MAX_DELAY = 60     # seconds

def ensure_output_dir(directory: str) -> None:
    """Ensure the output directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def compute_file_sha256(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_humaneval() -> str:
    """
    Download the full HumanEval dataset from HuggingFace.
    Uses streaming to handle potential size issues, though HumanEval is small.
    Implements exponential backoff retry logic.
    Returns the path to the saved parquet file.
    """
    ensure_output_dir(RAW_DATA_DIR)

    # Check if file already exists and is valid (optional optimization)
    if os.path.exists(PARQUET_PATH):
        logger.info(f"File {PARQUET_PATH} already exists. Skipping download.")
        # In a real scenario, we might verify the hash here, but for now we skip
        return PARQUET_PATH

    logger.info(f"Downloading dataset {DATASET_NAME} (revision={DATASET_REVISION})...")

    # Import datasets inside the function to handle dependency errors gracefully
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError(
            "The 'datasets' package is required. Please install it via: pip install datasets"
        )

    retry_count = 0
    current_delay = INITIAL_DELAY
    last_exception = None

    while retry_count < MAX_RETRIES:
        try:
            # Load the dataset with the specified revision
            # We use streaming=True to be safe, though we need to write to parquet
            ds = load_dataset(
                DATASET_NAME,
                split="test",
                revision=DATASET_REVISION,
                trust_remote_code=True
            )

            # Verify we have data
            if len(ds) == 0:
                raise RuntimeError("Downloaded dataset contains zero records.")

            logger.info(f"Successfully loaded {len(ds)} records from {DATASET_NAME}.")

            # Convert to pandas and then to parquet
            # datasets.Dataset has a .to_pandas() method
            df = ds.to_pandas()

            # Save to parquet
            df.to_parquet(PARQUET_PATH, index=False)
            logger.info(f"Saved dataset to {PARQUET_PATH}")

            # Compute checksum
            checksum = compute_file_sha256(PARQUET_PATH)
            logger.info(f"SHA256 checksum: {checksum}")

            return PARQUET_PATH

        except Exception as e:
            last_exception = e
            retry_count += 1
            logger.warning(f"Attempt {retry_count}/{MAX_RETRIES} failed: {e}")

            if retry_count < MAX_RETRIES:
                logger.info(f"Retrying in {current_delay} seconds...")
                time.sleep(current_delay)
                # Exponential backoff with max cap
                current_delay = min(current_delay * 2, MAX_DELAY)
            else:
                logger.error(f"Failed to download dataset after {MAX_RETRIES} attempts.")
                raise last_exception

    # Should not reach here
    raise RuntimeError("Download loop exited unexpectedly.")

def save_metadata(checksum: str, record_count: int) -> None:
    """
    Save dataset metadata to data/metadata.yaml.
    Includes version, file path, checksum, timestamp, and record count.
    """
    metadata = {
        "dataset_name": DATASET_NAME,
        "version": DATASET_REVISION,
        "file_path": f"data/raw/{PARQUET_FILENAME}",
        "sha256_checksum": checksum,
        "download_timestamp": datetime.utcnow().isoformat(),
        "record_count": record_count
    }

    # Write YAML manually to avoid dependency on PyYAML if not present,
    # though PyYAML is likely installed given the project context.
    # Using simple YAML formatting for robustness.
    yaml_content = []
    for key, value in metadata.items():
        yaml_content.append(f"{key}: {value}")

    yaml_text = "\n".join(yaml_content)

    ensure_output_dir(os.path.dirname(METADATA_FILE))
    with open(METADATA_FILE, "w") as f:
        f.write(yaml_text)

    logger.info(f"Metadata saved to {METADATA_FILE}")

def perform_stratified_sampling(data: Any, config: Dict, sample_output: str) -> None:
    """
    Placeholder for stratified sampling logic.
    The current task T010 focuses on downloading the FULL dataset.
    Stratified sampling is not required for T010 as per the description
    which asks for the "full HumanEval dataset".
    However, the previous implementation called this and failed due to missing config keys.
    Since T010 is about downloading the FULL dataset, we simply skip sampling.
    """
    logger.info("Skipping stratified sampling for T010 (Full Dataset Download).")
    # No-op for this task. The data is already saved in download_humaneval.

def main():
    """Main entry point for T010."""
    logger.info("Starting T010: Download HumanEval Dataset")

    try:
        # Download the dataset
        parquet_path = download_humaneval()

        # Load the saved parquet to get record count for metadata
        import pandas as pd
        df = pd.read_parquet(parquet_path)
        record_count = len(df)

        # Compute checksum again to be sure (or use the one from download if stored)
        checksum = compute_file_sha256(parquet_path)

        # Save metadata
        save_metadata(checksum, record_count)

        # Note: T010 does not require stratified sampling.
        # The previous error 'quartile_boundaries' came from a sampling step
        # that is not part of the core T010 requirement (Download FULL dataset).
        # If the pipeline requires sampling later, that should be a separate step or task.
        # For T010, we just ensure the full data is downloaded and metadata is recorded.

        logger.info("T010 completed successfully.")

    except Exception as e:
        logger.error(f"T010 failed: {e}")
        raise

if __name__ == "__main__":
    main()
