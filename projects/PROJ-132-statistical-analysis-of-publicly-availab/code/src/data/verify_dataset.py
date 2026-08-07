"""
Verify the existence of the vvud/eb-data dataset on HuggingFace.

This script attempts to list the 'vvud/eb-data' dataset using the datasets library.
If the dataset is not found or accessible, it raises a RuntimeError with a clear
message referencing the plan's scope note.

Dependency: T005a (Verify Full EBD Availability)
"""
import sys
import logging
from pathlib import Path

from datasets import load_dataset
from src.config import setup_logging

# Configure logging
logger = setup_logging(__name__)

DATASET_NAME = "vvud/eb-data"
PLAN_SCOPE_NOTE = (
    "Critical Data Scope Note: If the full eBird Basic Dataset (EBD) for North America "
    "(2020–2024) is unavailable via a verified public URL, the pipeline must proceed "
    "using the sample dataset 'vvud/eb-data' from HuggingFace. Do NOT fall back to "
    "synthetic data."
)

def verify_dataset_existence() -> bool:
    """
    Verify that the vvud/eb-data dataset exists on HuggingFace.

    Returns:
        True if the dataset exists and is accessible.

    Raises:
        RuntimeError: If the dataset cannot be found or accessed.
    """
    logger.info(f"Attempting to verify existence of dataset: {DATASET_NAME}")
    try:
        # Attempt to load the dataset info (metadata only) to verify existence
        # using streaming=False is fine for just checking existence, but we can
        # also use streaming=True to be safe. For existence check, we just need
        # to resolve the dataset info.
        ds = load_dataset(DATASET_NAME, streaming=True)
        
        # If we get here, the dataset exists and is accessible
        logger.info(f"SUCCESS: Dataset '{DATASET_NAME}' found and accessible on HuggingFace.")
        logger.info(f"Dataset info: {ds}")
        return True

    except Exception as e:
        error_msg = (
            f"CRITICAL: The verified sample dataset '{DATASET_NAME}' could not be found "
            f"or accessed on HuggingFace. This violates the plan's '{PLAN_SCOPE_NOTE}'. "
            f"Original error: {type(e).__name__}: {str(e)}"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def main():
    """
    Main entry point for the verification script.
    """
    logger.info("Starting dataset verification task (T051a)...")
    
    try:
        success = verify_dataset_existence()
        if success:
            logger.info("T051a VERIFICATION PASSED: Dataset exists.")
            sys.exit(0)
        else:
            # Should not reach here if exception is raised on failure
            logger.error("T051a VERIFICATION FAILED: Dataset check returned False.")
            sys.exit(1)
    except RuntimeError as e:
        logger.error(f"T051a VERIFICATION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {type(e).__name__}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()