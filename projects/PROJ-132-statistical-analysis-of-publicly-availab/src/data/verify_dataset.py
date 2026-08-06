"""
Verify the existence of the 'vvud/eb-data' dataset on HuggingFace.

This script attempts to list the dataset using the HuggingFace datasets library.
If the dataset is not found or accessible, it raises a RuntimeError.
"""
import sys
import logging
from pathlib import Path

# Add project root to path if necessary (for local execution)
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import setup_logging

# Configure logging
logger = setup_logging("verify_dataset")

DATASET_ID = "vvud/eb-data"

def verify_dataset_existence(dataset_id: str) -> bool:
    """
    Verify that a dataset exists on HuggingFace Hub.

    Args:
        dataset_id: The HuggingFace dataset identifier (e.g., "username/dataset-name").

    Returns:
        True if the dataset exists and is accessible.

    Raises:
        RuntimeError: If the dataset cannot be found or accessed.
    """
    try:
        from datasets import load_dataset
        from huggingface_hub import HfApi

        logger.info(f"Attempting to verify existence of dataset: {dataset_id}")

        # Method 1: Check via HfApi directly (lightweight check)
        api = HfApi()
        try:
            api.dataset_info(dataset_id=dataset_id)
            logger.info(f"Dataset '{dataset_id}' verified via HfApi.")
            return True
        except Exception as api_error:
            # If API check fails, try loading (which might handle auth differently)
            logger.warning(f"HfApi check failed: {api_error}. Attempting load_dataset...")

        # Method 2: Attempt to load with streaming (lightweight)
        # This forces a check of the dataset existence without downloading data
        ds = load_dataset(dataset_id, streaming=True)
        logger.info(f"Dataset '{dataset_id}' verified via load_dataset(streaming=True).")
        return True

    except Exception as e:
        error_msg = f"Dataset '{dataset_id}' not found or inaccessible: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def main():
    """Main entry point for the verification script."""
    logger.info("Starting dataset verification process.")
    try:
        if verify_dataset_existence(DATASET_ID):
            logger.info(f"SUCCESS: Dataset '{DATASET_ID}' exists.")
            return 0
    except RuntimeError as e:
        logger.error(f"FAILURE: {e}")
        return 1
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
