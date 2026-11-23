import os
import sys
import logging
import time
from typing import Optional, Tuple
from datasets import load_dataset

from config import get_config
from utils.logging_utils import setup_logging, get_logger
from utils.checksum_manager import calculate_sha256

# The specific Hugging Face dataset ID for the kinetic data required.
# This dataset contains experimental reaction rates for a curated set of molecules.
KINETIC_DATASET_ID = "moleculenet/reaction_rates_kinetic"
KINETIC_OUTPUT_FILENAME = "kinetic_dataset_raw.csv"

def setup_script_logging() -> logging.Logger:
    """Configure logging for the kinetic data download script."""
    logger = logging.getLogger("kinetic_download")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def download_kinetic_dataset(
    dataset_id: str = KINETIC_DATASET_ID,
    output_filename: str = KINETIC_OUTPUT_FILENAME,
    logger: Optional[logging.Logger] = None,
) -> Tuple[bool, str]:
    """
    Fetches the kinetic dataset from Hugging Face Datasets and saves it as a CSV.

    This function attempts to load the dataset using the `datasets` library.
    It does NOT use synthetic fallbacks. If the dataset is unavailable, it raises
    an exception to ensure the pipeline fails loudly as per requirements.

    Args:
        dataset_id: The Hugging Face dataset identifier.
        output_filename: The filename to save the CSV to (relative to data/raw).
        logger: Optional logger instance.

    Returns:
        Tuple of (success: bool, message: str)
    """
    if logger is None:
        logger = setup_script_logging()

    config = get_config()
    raw_dir = os.path.join(config["data_dir"], "raw")
    os.makedirs(raw_dir, exist_ok=True)
    output_path = os.path.join(raw_dir, output_filename)

    logger.info(f"Attempting to fetch dataset '{dataset_id}' from Hugging Face.")

    try:
        # Load the dataset. We assume the dataset provides a 'train' or 'full' split.
        # If the dataset structure is different, we adapt, but we do not fake data.
        dataset = load_dataset(dataset_id, split="train")
        
        logger.info(f"Dataset loaded successfully. Rows: {len(dataset)}")

        if len(dataset) < 20:
            logger.warning(f"Dataset contains only {len(dataset)} rows, which is less than the required 20.")
            # We proceed but log a warning. The task requirement is to fetch the dataset,
            # and if the source is small, we must report it, not inflate it.

        # Convert to pandas and save to CSV
        df = dataset.to_pandas()
        
        # Ensure required columns exist or log what we have
        logger.info(f"Columns in dataset: {list(df.columns)}")
        
        df.to_csv(output_path, index=False)
        
        logger.info(f"Successfully saved kinetic dataset to {output_path}")
        
        # Calculate and log checksum for immediate verification
        checksum = calculate_sha256(output_path)
        logger.info(f"SHA-256 checksum of saved file: {checksum}")

        return True, f"Downloaded and saved {len(df)} rows to {output_path}"

    except Exception as e:
        logger.error(f"Failed to download kinetic dataset: {e}")
        # Explicitly do NOT return a synthetic dataset or fallback.
        # The pipeline must fail loudly.
        raise RuntimeError(f"Critical failure fetching kinetic dataset from {dataset_id}: {e}")

def main():
    """Entry point for the kinetic data download script."""
    logger = setup_script_logging()
    logger.info("Starting kinetic dataset download process.")
    
    try:
        success, message = download_kinetic_dataset(logger=logger)
        if success:
            logger.info(f"Process completed: {message}")
            sys.exit(0)
        else:
            logger.error(f"Process failed: {message}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
