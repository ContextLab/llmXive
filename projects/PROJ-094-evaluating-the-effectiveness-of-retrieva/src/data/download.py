"""
Data download module for CodeSearchNet dataset.

This module handles the fetching of the CodeSearchNet dataset using ir_datasets.
It strictly distinguishes between training and test splits and saves them to
separate directories. It raises exceptions on failure and does NOT provide
synthetic fallbacks.
"""

import os
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import ir_datasets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this file (assuming src/data/download.py)
# We assume the project root is the parent of 'src'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
TRAIN_DIR = DATA_RAW_DIR / "train"
TEST_DIR = DATA_RAW_DIR / "test"

# Dataset identifiers for CodeSearchNet Python subset
# Using the specific subset identifiers for Python language
DATASET_TRAIN_ID = "codesearchnet-python/train"
DATASET_TEST_ID = "codesearchnet-python/test"

def ensure_directories() -> None:
    """Ensure that the raw data directories exist."""
    for directory in [DATA_RAW_DIR, TRAIN_DIR, TEST_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

def load_dataset_subset(dataset_id: str, split: str = "train") -> ir_datasets.Dataset:
    """
    Load a specific dataset subset using ir_datasets.

    Args:
        dataset_id: The ir_datasets identifier (e.g., "codesearchnet-python/train")
        split: The split name (though ir_datasets handles this via the ID usually)

    Returns:
        An ir_datasets.Dataset object.

    Raises:
        ValueError: If the dataset ID is invalid or not found.
        RuntimeError: If the dataset cannot be loaded due to network or other errors.
    """
    logger.info(f"Attempting to load dataset: {dataset_id}")
    try:
        dataset = ir_datasets.load(dataset_id)
        logger.info(f"Successfully loaded dataset: {dataset_id}")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {e}")
        raise RuntimeError(f"Failed to load dataset {dataset_id}: {e}") from e

def download_and_save_subset(dataset_id: str, output_dir: Path, subset_name: str) -> Dict[str, Any]:
    """
    Download a dataset subset and save it to JSONL files.

    This function iterates through the dataset items and saves them to a JSONL file.
    It calculates a checksum for the saved file for verification.

    Args:
        dataset_id: The ir_datasets identifier.
        output_dir: The directory to save the data.
        subset_name: A name for the subset (e.g., "python").

    Returns:
        A dictionary containing metadata about the download.

    Raises:
        RuntimeError: If the download or save process fails.
    """
    logger.info(f"Starting download and save for {dataset_id} to {output_dir}")
    ensure_directories()

    dataset = load_dataset_subset(dataset_id)

    output_file = output_dir / f"{subset_name}.jsonl"
    item_count = 0
    checksum = None

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in dataset:
                # Convert the item (which might be a dict-like object) to a JSON string
                # ir_datasets items are often namedtuples or dicts. We convert to dict.
                item_dict = {}
                for key in item._fields:
                    value = getattr(item, key)
                    # Ensure value is JSON serializable
                    if isinstance(value, bytes):
                        value = value.decode('utf-8', errors='replace')
                    item_dict[key] = value
                
                f.write(json.dumps(item_dict) + '\n')
                item_count += 1

        # Calculate checksum
        with open(output_file, 'rb') as f:
            content = f.read()
            checksum = hashlib.sha256(content).hexdigest()

        logger.info(f"Saved {item_count} items to {output_file}")
        logger.info(f"Checksum: {checksum}")

        return {
            "dataset_id": dataset_id,
            "output_file": str(output_file),
            "item_count": item_count,
            "checksum": checksum,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error during download/save of {dataset_id}: {e}")
        # Clean up partial file if it exists
        if output_file.exists():
            output_file.unlink()
        raise RuntimeError(f"Failed to download and save {dataset_id}: {e}") from e

def verify_download(output_dir: Path, expected_count: Optional[int] = None) -> bool:
    """
    Verify that the downloaded files exist and are non-empty.

    Args:
        output_dir: The directory containing the downloaded files.
        expected_count: Optional expected number of items (not strictly enforced here, just existence).

    Returns:
        True if verification passes, False otherwise.
    """
    logger.info(f"Verifying download in {output_dir}")
    if not output_dir.exists():
        logger.error(f"Directory {output_dir} does not exist")
        return False

    files = list(output_dir.glob("*.jsonl"))
    if not files:
        logger.error(f"No JSONL files found in {output_dir}")
        return False

    for f in files:
        if f.stat().st_size == 0:
            logger.error(f"File {f} is empty")
            return False

    logger.info(f"Verification passed. Found {len(files)} non-empty JSONL files.")
    return True

def main() -> None:
    """
    Main entry point for the download script.

    This function orchestrates the downloading of both train and test splits
    of the CodeSearchNet Python dataset.
    """
    logger.info("Starting CodeSearchNet download process")

    ensure_directories()

    # Define download tasks
    tasks = [
        {
            "dataset_id": DATASET_TRAIN_ID,
            "output_dir": TRAIN_DIR,
            "subset_name": "python_train"
        },
        {
            "dataset_id": DATASET_TEST_ID,
            "output_dir": TEST_DIR,
            "subset_name": "python_test"
        }
    ]

    results = []
    success = True

    for task in tasks:
        try:
            result = download_and_save_subset(
                task["dataset_id"],
                task["output_dir"],
                task["subset_name"]
            )
            results.append(result)
            
            # Verify immediately after download
            if not verify_download(task["output_dir"]):
                logger.error(f"Verification failed for {task['dataset_id']}")
                success = False
        except Exception as e:
            logger.error(f"Critical error processing {task['dataset_id']}: {e}")
            success = False
            # Do not fallback, just fail
            break

    # Save summary
    summary_file = DATA_RAW_DIR / "download_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "status": "success" if success else "failed",
            "results": results
        }, f, indent=2)

    if success:
        logger.info("All downloads completed successfully")
    else:
        logger.error("One or more downloads failed. Check logs.")
        raise RuntimeError("Download process failed. See logs for details.")

if __name__ == "__main__":
    main()
