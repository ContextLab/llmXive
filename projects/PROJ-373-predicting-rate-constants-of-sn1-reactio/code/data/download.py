"""
code/data/download.py

Fetches verified SN1 kinetic datasets from HuggingFace and merges them into a single Parquet file.
Implements strict failure handling: exits with code 1 if the pipeline status is 'ABORTED' or if the download fails.
No synthetic fallbacks are permitted.
"""
import os
import sys
import logging
import argparse
import time
from pathlib import Path
from typing import Optional, Dict, Any

# Import from project modules
from config import DataConfig, ensure_dirs
from utils.logger import get_logger

# Attempt to import datasets; if missing, we fail loudly as per requirements
try:
    from datasets import load_dataset
except ImportError:
    print("CRITICAL: 'datasets' library not found. Please install it via 'pip install datasets'.")
    sys.exit(1)

# Configuration
DATASET_NAMES = [
    "DTS-SN1-15-01-2024",
    "SN18-All-20240204"
]
PIPELINE_STATUS_PATH = "data/processed/.pipeline_status"
OUTPUT_DIR = "data/raw"
OUTPUT_FILE = "sn1_raw_merged.parquet"

# Logger setup
logger = get_logger("download")

def check_pipeline_status() -> bool:
    """
    Checks the pipeline status file.
    Returns True if status is 'OK'.
    Returns False and exits with code 1 if status is 'ABORTED' or missing.
    """
    status_path = Path(PIPELINE_STATUS_PATH)
    if not status_path.exists():
        logger.error(f"Pipeline status file not found: {status_path}. Aborting.")
        sys.exit(1)

    try:
        status = status_path.read_text().strip()
    except Exception as e:
        logger.error(f"Failed to read pipeline status: {e}")
        sys.exit(1)

    if status == "ABORTED":
        logger.error("Pipeline status is 'ABORTED'. Aborting download.")
        sys.exit(1)
    elif status == "OK":
        return True
    else:
        logger.warning(f"Unknown pipeline status '{status}'. Proceeding with caution, but expected 'OK'.")
        return True

def download_dataset_with_streaming(dataset_name: str, split: str = "train") -> Optional[Any]:
    """
    Downloads a dataset from HuggingFace using streaming mode.
    Returns the dataset object or None if it fails.
    """
    logger.info(f"Attempting to download dataset: {dataset_name}")
    try:
        # Use streaming to handle large datasets without loading fully into memory immediately
        dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=True,
            trust_remote_code=True
        )
        logger.info(f"Successfully connected to dataset: {dataset_name}")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        return None

def get_dataset_size_estimate(dataset_name: str) -> int:
    """
    Estimates dataset size in bytes.
    For now, returns a placeholder or attempts to get info if possible.
    Since we are streaming, we might not know the exact size upfront without iterating.
    We will proceed with the download logic assuming we can stream.
    """
    # Placeholder: In a real scenario, we might check HuggingFace hub info.
    # For this task, we focus on the download logic.
    return 0

def download_with_retry(dataset_name: str, output_path: Path, max_retries: int = 3) -> bool:
    """
    Downloads the dataset and saves it to the output path.
    Implements a simple retry mechanism for transient network errors.
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Download attempt {attempt + 1}/{max_retries} for {dataset_name}")
            dataset = download_dataset_with_streaming(dataset_name)
            
            if dataset is None:
                raise Exception("Dataset load returned None")

            # Since we are streaming, we need to collect the data or write it directly.
            # For Parquet, it's often easier to collect to a list of dicts or a pandas DataFrame
            # if memory permits, or write in chunks.
            # Given the constraint of "real data" and potential size, we will try to stream to a list
            # first, but if it's too large, we might need a chunked approach.
            # For this implementation, we assume we can iterate and convert to a format suitable for saving.
            
            # Collecting data for merging
            # Note: If the dataset is huge, this might OOM. However, the task requires producing the file.
            # We will attempt to iterate and build a list of rows.
            rows = []
            count = 0
            for row in dataset:
                rows.append(row)
                count += 1
                if count % 10000 == 0:
                    logger.info(f"Downloaded {count} rows...")
            
            logger.info(f"Finished downloading {count} rows for {dataset_name}")
            
            # We return the rows and the dataset name to be merged later
            return rows, dataset_name

        except Exception as e:
            logger.error(f"Error during download attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt) # Exponential backoff
            else:
                logger.error(f"Failed to download {dataset_name} after {max_retries} attempts.")
                return None

def main():
    """
    Main entry point for the download script.
    """
    parser = argparse.ArgumentParser(description="Download SN1 datasets")
    parser.add_argument("--dataset", type=str, help="Specific dataset to download (optional)")
    parser.add_argument("--output", type=str, help="Output file path (optional)")
    parser.add_argument("--schema-log", type=str, help="Path to schema check log (optional)")
    args = parser.parse_args()

    # Ensure output directory exists
    ensure_dirs(Path(OUTPUT_DIR))

    # Check pipeline status
    if not check_pipeline_status():
        # check_pipeline_status exits if aborted, but for safety:
        sys.exit(1)

    datasets_to_process = [args.dataset] if args.dataset else DATASET_NAMES
    all_rows = []
    
    for ds_name in datasets_to_process:
        result = download_with_retry(ds_name, Path(OUTPUT_DIR) / OUTPUT_FILE)
        if result is None:
            logger.error(f"Fatal error: Failed to download {ds_name}. Aborting pipeline.")
            # Write ABORTED status
            Path(PIPELINE_STATUS_PATH).write_text("ABORTED")
            sys.exit(1)
        
        rows, name = result
        all_rows.extend(rows)
        logger.info(f"Collected {len(rows)} rows from {name}")

    if not all_rows:
        logger.error("No data collected from any dataset. Aborting.")
        Path(PIPELINE_STATUS_PATH).write_text("ABORTED")
        sys.exit(1)

    # Merge and save to Parquet
    import pandas as pd
    logger.info(f"Merging {len(all_rows)} rows into Parquet file...")
    df = pd.DataFrame(all_rows)
    
    output_path = Path(args.output) if args.output else Path(OUTPUT_DIR) / OUTPUT_FILE
    # Ensure the output file path is correct
    if not str(output_path).endswith(".parquet"):
        output_path = Path(str(output_path) + ".parquet")
    
    try:
        df.to_parquet(output_path, index=False)
        logger.info(f"Successfully saved merged data to {output_path}")
        logger.info(f"Total rows saved: {len(df)}")
        logger.info(f"Columns: {list(df.columns)}")
    except Exception as e:
        logger.error(f"Failed to save Parquet file: {e}")
        Path(PIPELINE_STATUS_PATH).write_text("ABORTED")
        sys.exit(1)

    logger.info("Download and merge completed successfully.")

if __name__ == "__main__":
    main()