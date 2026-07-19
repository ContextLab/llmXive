"""
Data download module for fetching the GFA dataset from HuggingFace.

This module implements the fetch logic for the 'Recent Experimental GFA' dataset.
It includes retry logic, error handling, and SHA-256 verification as per FR-001.
"""
import os
import logging
import time
from pathlib import Path
from typing import Optional

try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("The 'datasets' package is required. Install it via: pip install datasets")

from config.environment import get_environment_config
from data.checksums import generate_checksum, save_checksum
from utils.logger import get_logger, DataDownloadError

logger = get_logger("data.download")

# Constants for retry logic
MAX_RETRIES = 5
RETRY_BASE_DELAY = 5  # seconds

def verify_schema(df: 'pd.DataFrame') -> bool:
    """
    Verifies that the DataFrame contains the required columns.
    Raises an exception if the schema is invalid.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required for schema verification")

    required_cols = {'composition'}
    optional_cols = {'log10_Rc', 'Rc'}
    
    # We need at least one of the target columns
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")
    
    if not (optional_cols & set(df.columns)):
        raise ValueError(
            f"Dataset must contain either 'log10_Rc' or 'Rc' column. "
            f"Found columns: {list(df.columns)}"
        )
    
    logger.info("Schema verification passed.")
    return True

def download_gfa_dataset(output_dir: str) -> str:
    """
    Fetches the 'Recent Experimental GFA' dataset from HuggingFace and saves it to the specified directory.
    
    Args:
        output_dir: Path to the directory where the CSV should be saved.
        
    Returns:
        Path to the downloaded CSV file.
        
    Raises:
        DataDownloadError: If the dataset cannot be fetched, saved, or verified after retries.
    """
    config = get_environment_config()
    # Use the verified dataset ID from config or fallback to the known source
    dataset_name = config.dataset_name or "ml4matscience/gfa-experimental"
    
    output_path = Path(output_dir) / "gfa_dataset.csv"
    checksum_path = Path(output_dir) / "gfa_dataset.csv.sha256"
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    if output_path.exists():
        logger.info(f"Dataset already exists at {output_path}. Skipping download.")
        # Verify existing checksum if available
        if checksum_path.exists():
            logger.info("Existing checksum file found.")
        else:
            logger.warning("Existing dataset found but no checksum file. Regenerating checksum.")
            save_checksum(str(output_path), str(checksum_path))
        return str(output_path)

    logger.info(f"Attempting to download dataset: {dataset_name}")
    
    last_exception = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Download attempt {attempt}/{MAX_RETRIES}")
            
            # Load the dataset
            # Note: We use streaming=False to ensure we get the full dataset for processing
            dataset = load_dataset(dataset_name, split="train", trust_remote_code=True)
            
            # Convert to pandas and save to CSV
            df = dataset.to_pandas()
            
            if df.empty:
                raise ValueError("Downloaded dataset is empty.")
            
            # Schema Verification: Must happen BEFORE saving checksum
            verify_schema(df)
            
            df.to_csv(output_path, index=False)
            
            logger.info(f"Dataset downloaded and saved to {output_path} ({len(df)} rows).")
            
            # Generate and save checksum ONLY after schema verification passes
            save_checksum(str(output_path), str(checksum_path))
            logger.info(f"Checksum saved to {checksum_path}")
            
            return str(output_path)
            
        except Exception as e:
            last_exception = e
            error_msg = str(e)
            logger.error(f"Attempt {attempt} failed: {e}")
            
            # Explicit handling for 401/403 errors
            if "401" in error_msg or "403" in error_msg or "Authentication" in error_msg or "Permission" in error_msg:
                logger.critical(f"Authentication/Permission error detected: {e}. Halting immediately.")
                raise DataDownloadError(f"Dataset access denied (401/403). Check dataset visibility or credentials: {e}")
            
            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                logger.info(f"Retrying in {delay} seconds (exponential backoff)...")
                time.sleep(delay)
            else:
                logger.error("Max retries reached. Download failed.")
    
    raise DataDownloadError(f"Dataset download failed after {MAX_RETRIES} attempts: {last_exception}")

def main():
    """Main entry point for standalone execution."""
    config = get_environment_config()
    output_dir = config.raw_data_dir
    logger.info(f"Starting dataset download to {output_dir}")
    result_path = download_gfa_dataset(output_dir)
    logger.info(f"Download completed successfully: {result_path}")

if __name__ == "__main__":
    main()