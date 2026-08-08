"""
T051a: Verify the existence of the vvud/eb-data dataset on HuggingFace.

This script attempts to list the 'vvud/eb-data' dataset using the HuggingFace
datasets library. If the dataset is not found or inaccessible, it raises a
RuntimeError with a clear message referencing the plan's "Critical Data Scope Note".

The script must fail loudly (raise an exception) rather than falling back to
synthetic data or a mock.
"""
import sys
import logging
from pathlib import Path

# Import local config for logging setup
# Note: The API surface shows src/config is available
try:
    from src.config import setup_logging
except ImportError:
    # Fallback if src is not in path during direct execution
    import os
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from src.config import setup_logging

from datasets import load_dataset

# Configure logger
logger = setup_logging()

DATASET_NAME = "vvud/eb-data"

def verify_dataset_existence() -> bool:
    """
    Verifies the existence of the specified dataset on HuggingFace.
    
    Returns:
        True if the dataset is found and accessible.
        
    Raises:
        RuntimeError: If the dataset cannot be found or accessed.
    """
    logger.info(f"Verifying existence of dataset: {DATASET_NAME}")
    
    try:
        # Attempt to list the dataset info without downloading data
        # We use load_dataset with streaming=False but just checking info
        # or simply trying to load the config list.
        # The most robust way to "verify existence" before download is to try loading the dataset builder.
        
        # We try to load the dataset with streaming=True to check connectivity
        # but we don't process it here. We just ensure the handle is valid.
        # Using a timeout isn't directly available in load_dataset for the initial handshake 
        # in older versions, but the library will raise an error if not found.
        
        # We request a minimal subset to verify access without heavy IO
        ds = load_dataset(
            DATASET_NAME, 
            split="train", 
            streaming=True, 
            trust_remote_code=True,
            download_mode="force_redownload" # Ensure we hit the network
        )
        
        # If we get here, the dataset exists and is accessible.
        # We don't iterate to save time, just confirming the handle is valid.
        logger.info(f"Successfully verified dataset: {DATASET_NAME}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to verify dataset {DATASET_NAME}: {error_msg}")
        
        # Specific check for 404 or dataset not found errors
        if "Dataset not found" in error_msg or "404" in error_msg or "Repository Not Found" in error_msg:
            raise RuntimeError(
                f"CRITICAL FAILURE: The dataset '{DATASET_NAME}' does not exist on HuggingFace. "
                f"This violates the 'Critical Data Scope Note' in plan.md which mandates this specific source. "
                f"Please verify the dataset ID or network access. Original error: {error_msg}"
            ) from e
        
        # For network issues or other errors, we still fail loudly as per requirements
        raise RuntimeError(
            f"CRITICAL FAILURE: Unable to access dataset '{DATASET_NAME}' from HuggingFace. "
            f"Real data source verification failed. Original error: {error_msg}"
        ) from e

def main():
    """Main entry point for T051a."""
    verify_dataset_existence()
    logger.info("T051a Verification Complete: Dataset exists and is accessible.")

if __name__ == "__main__":
    main()
