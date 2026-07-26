"""
Download the RepoPeftBench Python subset from HuggingFace.

This script fetches the real 'python' subset of the RepoPeftBench dataset
and saves it to data/raw/repopeftbench_python/ in parquet format.

It verifies the dataset integrity by checking for the presence of required
columns and non-empty rows. No synthetic data is generated.
"""

import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import setup_logging, get_logger

# Configure logging
logger = get_logger(__name__)

# Constants
DATASET_NAME = "repo-peft-bench"
CONFIG_NAME = "python"
OUTPUT_DIR = project_root / "data" / "raw" / "repopeftbench_python"
REQUIRED_COLUMNS = ["task_id", "instruction", "input_code", "expected_output", "test_code"]
CHECKSUM_FILE = OUTPUT_DIR / ".checksums.json"

def verify_dataset_integrity(dataset: Any) -> bool:
    """
    Verify that the loaded dataset has the required columns and data.
    
    Args:
        dataset: The loaded HuggingFace dataset object.
        
    Returns:
        True if verification passes, False otherwise.
    """
    if not hasattr(dataset, 'features'):
        logger.error("Dataset object does not have 'features' attribute.")
        return False
    
    features = dataset.features
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in features]
    
    if missing_columns:
        logger.error(f"Dataset is missing required columns: {missing_columns}")
        return False
    
    # Check if dataset is empty
    if len(dataset) == 0:
        logger.error("Dataset is empty.")
        return False
    
    logger.info(f"Dataset verification passed. Found {len(dataset)} examples.")
    return True

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset() -> bool:
    """
    Download the RepoPeftBench Python dataset from HuggingFace.
    
    Returns:
        True if download and verification succeed, False otherwise.
    """
    logger.info(f"Starting download of {DATASET_NAME} ({CONFIG_NAME})...")
    
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is required. Install it with: pip install datasets")
        return False

    try:
        # Load the dataset (streaming=False to ensure full download for verification)
        # This will download to the local cache automatically
        logger.info("Loading dataset from HuggingFace...")
        dataset = load_dataset(DATASET_NAME, CONFIG_NAME, split="train")
        
        if not verify_dataset_integrity(dataset):
            logger.error("Dataset verification failed. Aborting save.")
            return False

        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save the dataset to parquet format
        output_path = OUTPUT_DIR / "dataset.parquet"
        logger.info(f"Saving dataset to {output_path}...")
        dataset.to_parquet(str(output_path))
        
        # Compute and save checksum
        if output_path.exists():
            checksum = compute_file_checksum(output_path)
            checksum_data = {
                "file": "dataset.parquet",
                "sha256": checksum,
                "num_examples": len(dataset)
            }
            
            import json
            with open(CHECKSUM_FILE, "w") as f:
                json.dump(checksum_data, f, indent=2)
            
            logger.info(f"Dataset saved successfully with {len(dataset)} examples.")
            logger.info(f"Checksum: {checksum}")
            return True
        else:
            logger.error("Failed to save dataset file.")
            return False

    except Exception as e:
        logger.error(f"Error downloading or processing dataset: {e}", exc_info=True)
        return False

def main():
    """Main entry point for the script."""
    setup_logging(level=logging.INFO)
    
    logger.info(f"RepoPeftBench Python Downloader starting.")
    logger.info(f"Target directory: {OUTPUT_DIR}")
    
    success = download_dataset()
    
    if success:
        logger.info("Download and verification completed successfully.")
        sys.exit(0)
    else:
        logger.error("Download failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
