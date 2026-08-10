import os
import sys
import json
import time
import logging
import hashlib
import subprocess
from typing import Optional, List, Dict, Any

# Import shared utilities from utils
from utils import setup_logging, get_logger, set_task_id, get_task_id, compute_sha256

# Constants
DATASET_NAME = "openai/openai_humaneval"
DATASET_SPLIT = "test"
DATASET_REVISION = "main"
MAX_RETRIES = 3
RETRY_DELAY = 5
OUTPUT_JSON = "data/raw/humaneval.json"
OUTPUT_PARQUET = "data/raw/humaneval.parquet"
OUTPUT_CHECKSUM = "data/raw/humaneval.sha256"

# Ensure output directory exists
def ensure_output_dir(output_path: str) -> None:
    """Create the directory for the output file if it doesn't exist."""
    dir_name = os.path.dirname(output_path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
        get_logger().info(f"Created directory: {dir_name}")

def download_humaneval() -> List[Dict[str, Any]]:
    """
    Download the full HumanEval dataset from HuggingFace.
    Uses the verified recipe: load_dataset("openai/openai_humaneval", split="test", revision="main").
    Raises RuntimeError if download fails after max retries.
    """
    logger = get_logger()
    logger.info(f"Downloading {DATASET_NAME} (split={DATASET_SPLIT}, revision={DATASET_REVISION})...")

    retry_count = 0
    last_exception = None

    while retry_count < MAX_RETRIES:
        try:
            # Verify dependency is installed
            try:
                from datasets import load_dataset
            except ImportError:
                raise RuntimeError("The 'datasets' package is required. Install it via 'pip install datasets'")

            # Load the dataset using the verified recipe with deterministic revision
            ds = load_dataset(DATASET_NAME, split=DATASET_SPLIT, revision=DATASET_REVISION)

            # Validate we got data
            if len(ds) == 0:
                raise RuntimeError("Loaded dataset contains zero records")

            # Convert to list of dicts
            data = ds.to_list()
            logger.info(f"Successfully downloaded {len(data)} records.")
            return data

        except Exception as e:
            last_exception = e
            retry_count += 1
            logger.warning(f"Download attempt {retry_count}/{MAX_RETRIES} failed: {e}")
            if retry_count < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Max retries reached. Download failed.")

    # If we get here, all retries failed
    raise RuntimeError("Failed to download verified real source")

def save_to_jsonl(data: List[Dict[str, Any]], output_path: str) -> None:
    """Save the dataset as a JSONL file."""
    ensure_output_dir(output_path)
    logger = get_logger()
    logger.info(f"Saving {len(data)} records to {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        for record in data:
            # Ensure keys are sorted for deterministic output
            json.dump(record, f, sort_keys=True)
            f.write('\n')

    logger.info(f"Saved JSONL to {output_path}")

def save_to_parquet(data: List[Dict[str, Any]], output_path: str) -> None:
    """Convert JSONL to Parquet format using pandas and pyarrow."""
    ensure_output_dir(output_path)
    logger = get_logger()
    logger.info(f"Converting to Parquet and saving to {output_path}...")

    try:
        import pandas as pd
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        raise RuntimeError("pandas and pyarrow are required for Parquet conversion. Install via 'pip install pandas pyarrow'")

    df = pd.DataFrame(data)
    table = pa.Table.from_pandas(df)
    pq.write_table(table, output_path)

    logger.info(f"Saved Parquet to {output_path}")

def verify_file_integrity(file_path: str, hash_path: str) -> None:
    """Compute SHA256 of the file and save it to hash_path."""
    logger = get_logger()
    logger.info(f"Computing SHA256 for {file_path}...")
    sha256_hash = compute_sha256(file_path)
    logger.info(f"SHA256: {sha256_hash}")

    with open(hash_path, 'w') as f:
        f.write(sha256_hash)

    logger.info(f"Saved checksum to {hash_path}")

def perform_stratified_sampling(data: List[Dict[str, Any]], config: Dict[str, Any], output_path: str) -> List[Dict[str, Any]]:
    """
    Placeholder for stratified sampling logic.
    Since the task requires the FULL dataset (N=164) and no sampling config is provided,
    we return the full data. If a config with 'quartile_boundaries' is passed, we would
    implement sampling logic here.
    """
    logger = get_logger()
    # Check if config expects stratified sampling
    if 'quartile_boundaries' in config:
        logger.warning("Stratified sampling requested but not fully implemented for this task. Returning full dataset.")
        # In a real scenario, we would filter based on quartile_boundaries
        # For now, we just return the full data to satisfy the "full dataset" requirement
        return data
    return data

def main():
    """Main entry point for T010."""
    # Initialize logging
    logger = setup_logging(task_id="T010")
    logger.info("Starting T010: Data Download and Conversion")

    try:
        # 1. Download the full HumanEval dataset
        data = download_humaneval()

        # 2. Save to JSON (JSONL format) - Task requires .json extension but content is JSONL
        # The task description says "Save raw data to data/raw/humaneval.json"
        # We will save it as JSONL format with .json extension as per task spec
        json_output = OUTPUT_JSON
        save_to_jsonl(data, json_output)

        # 3. Convert to Parquet
        parquet_output = OUTPUT_PARQUET
        save_to_parquet(data, parquet_output)

        # 4. Compute and save SHA256 checksum
        checksum_output = OUTPUT_CHECKSUM
        verify_file_integrity(parquet_output, checksum_output)

        logger.info("T010 completed successfully.")

    except RuntimeError as e:
        logger.error(f"Fatal error: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during T010: {e}")
        raise

if __name__ == "__main__":
    main()
