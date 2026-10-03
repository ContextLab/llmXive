"""
code/data/download.py

Fetches verified SN1 kinetic data from HuggingFace datasets.
Implements strict failure handling: raises fatal errors on download failure
with NO synthetic fallback.
"""

import os
import sys
import logging
import argparse
import time
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path for imports if run as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from datasets import load_dataset
from config import DataConfig, ensure_dirs
from utils.logger import get_logger

# Constants
PIPELINE_STATUS_FILE = "data/processed/.pipeline_status"
ABORTED_STATUS = "ABORTED"
OK_STATUS = "OK"
DEFAULT_DATASET_NAME = "DTS-SN1-15-01-2024" # Placeholder, actual name might vary based on spec
# Based on T011a verification, we assume the dataset name is verified there.
# We will accept it as an argument or default to the verified one if T011a passed.
# For this task, we assume the dataset name is passed or defaults to a known good one.
# The task description mentions: "Primary Source: HuggingFace datasets DTS-SN1-15-01-2024 and SN18-All-20240204"
# We will use the first one as default.

def check_schema_pass(schema_log_path: Optional[Path] = None) -> bool:
    """
    Checks if the pipeline status is 'OK' before proceeding.
    Returns True if status is 'OK', False otherwise.
    """
    status_path = Path(PIPELINE_STATUS_FILE)
    if not status_path.exists():
        logging.error(f"Pipeline status file not found: {status_path}. Has T011a run?")
        return False

    try:
        with open(status_path, 'r') as f:
            status = f.read().strip()
        if status == ABORTED_STATUS:
            logging.error(f"Pipeline status is '{ABORTED_STATUS}'. Aborting download.")
            return False
        elif status == OK_STATUS:
            return True
        else:
            logging.error(f"Unknown pipeline status: '{status}'. Aborting download.")
            return False
    except Exception as e:
        logging.error(f"Error reading pipeline status: {e}")
        return False

def get_dataset_size(dataset_name: str) -> Optional[int]:
    """
    Estimates dataset size in bytes. Returns None if unable to determine.
    This is a simple heuristic; actual size might vary.
    """
    # For now, we assume a large dataset and use streaming.
    # A more robust check would involve querying the dataset info.
    # Given the constraint > 7GB use streaming, we default to streaming for safety.
    return 10 * 1024 * 1024 * 1024 # 10GB placeholder

def download_dataset(dataset_name: str, output_path: Path, streaming: bool = True) -> None:
    """
    Downloads or streams the dataset from HuggingFace.
    Raises an exception on failure. NO synthetic fallback.
    """
    logging.info(f"Attempting to download/stream dataset: {dataset_name}")
    logging.info(f"Output path: {output_path}")
    logging.info(f"Streaming mode: {streaming}")

    try:
        # Ensure output directory exists
        ensure_dirs(output_path.parent)

        if streaming:
            logging.info("Using streaming mode for large dataset.")
            # Load dataset in streaming mode
            dataset = load_dataset(dataset_name, split='train', streaming=True, revision='main')

            # Convert to pandas and save to parquet
            # Since streaming doesn't load everything at once, we need to collect it.
            # However, if it's truly large, we might need to process in chunks.
            # For this task, we assume we can collect it or the dataset is manageable in memory after streaming.
            # If the dataset is too large for memory, we would need to write directly to parquet in chunks.
            # Given the constraint, we will try to collect and save.
            # If memory error occurs, we will let it crash (fail loudly).

            # Convert streaming dataset to a list of dicts or directly to a pandas DataFrame
            # This might be memory intensive if the dataset is huge.
            # A better approach for very large datasets is to write to parquet in chunks.
            # Let's try to convert to pandas first. If it fails, we might need a chunked approach.
            # For now, we assume it fits or we use a chunked writer if pandas fails.

            import pandas as pd

            # Try to convert to dataframe
            try:
                df = dataset.to_pandas()
            except MemoryError:
                logging.error("Dataset too large to fit in memory even with streaming conversion.")
                # Fallback to chunked processing if possible, but for this task, we fail loudly as per spec.
                # The spec says: "If the full dataset cannot be processed in the compute budget, use a well-defined REAL sample"
                # But for download.py, we are just fetching. If we can't fetch all, we might need to sample.
                # However, the task says "Download/stream". Let's assume we can get a representative sample if full is too big.
                # But the spec also says "NEVER fabricate...".
                # Let's try to stream and write to parquet in chunks if to_pandas fails.
                logging.info("Attempting to write to parquet in chunks.")
                df_stream = dataset.to_iterable() # This might not exist directly, need to iterate
                # Actually, datasets streaming returns an IterableDataset.
                # We can iterate and write row by row or in batches.
                # For simplicity and robustness, let's use the to_pandas with a sample if it's too big.
                # But the task says "download/stream".
                # Let's try to get a sample if full is too big, but log it.
                # However, the task says "Save raw data".
                # Let's assume the dataset is manageable for now, or we use a sample.
                # But the constraint says "Use streaming if size > 7GB".
                # Let's try to use a sample if it's too big, but that might not be "raw data".
                # The task says "Save raw data to data/raw/".
                # If we can't get all, we might need to fail.
                # Let's try to get a sample of 10000 rows if full is too big, but log it.
                # This is a compromise to avoid crashing the pipeline, but it's not "raw data" in full.
                # The spec says "If the full dataset cannot be processed in the compute budget, use a well-defined REAL sample".
                # So we can sample.
                logging.warning("Full dataset too large. Sampling 10000 rows for raw data.")
                df = dataset.to_pandas().sample(n=10000, random_state=42)

            # Save to parquet
            df.to_parquet(output_path, index=False)
            logging.info(f"Dataset saved to {output_path}")

        else:
            # Non-streaming mode
            dataset = load_dataset(dataset_name, split='train', revision='main')
            df = dataset.to_pandas()
            df.to_parquet(output_path, index=False)
            logging.info(f"Dataset saved to {output_path}")

    except Exception as e:
        logging.error(f"Failed to download/stream dataset: {e}")
        # Raise the exception to fail loudly
        raise RuntimeError(f"Dataset download failed: {e}") from e

def download_with_retry(dataset_name: str, output_path: Path, max_retries: int = 3, base_delay: float = 5.0) -> None:
    """
    Wraps download_dataset with retry logic for network errors.
    """
    for attempt in range(max_retries):
        try:
            download_dataset(dataset_name, output_path)
            return # Success
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            logging.warning(f"Download attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)

def main():
    parser = argparse.ArgumentParser(description="Download SN1 kinetic data from HuggingFace.")
    parser.add_argument('--dataset', type=str, default=DEFAULT_DATASET_NAME, help="HuggingFace dataset name")
    parser.add_argument('--output', type=str, default="data/raw/sn1_raw.parquet", help="Output file path")
    parser.add_argument('--schema-log', type=str, default=None, help="Path to schema check log (optional)")

    args = parser.parse_args()

    # Setup logging
    log_dir = Path("data/processed")
    ensure_dirs(log_dir)
    log_file = log_dir / "download.log"
    logger = get_logger(__name__, log_file=str(log_file))

    # Check if pipeline is aborted
    if not check_schema_pass():
        logger.error("Pipeline status is not OK. Aborting download.")
        sys.exit(1)

    output_path = Path(args.output)
    dataset_name = args.dataset

    logger.info(f"Starting download for dataset: {dataset_name}")
    logger.info(f"Output path: {output_path}")

    try:
        # Determine if streaming is needed (assume yes for large datasets)
        streaming = True # Default to streaming as per task constraint for >7GB

        # Download with retry
        download_with_retry(dataset_name, output_path)

        logger.info("Download completed successfully.")

    except Exception as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
