"""
Verification script for the raw bronze data artifact.
This script explicitly verifies that data/raw/bronze.parquet exists and is readable.
It is a dependency for T011 (preprocess.py).
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

from config import get_path, init_logger

# Initialize logger
logger = init_logger(__name__)

def verify_bronze_parquet():
    """
    Verify that the bronze parquet file exists and is readable.
    Raises RuntimeError if the file is missing or corrupted.
    """
    file_path = get_path("data", "raw", "bronze.parquet")
    path_obj = Path(file_path)

    # Check existence
    if not path_obj.exists():
        raise RuntimeError(
            f"CRITICAL: Artifact verification failed. "
            f"File '{file_path}' does not exist. "
            f"Please ensure T007 (ingest.py) has run successfully and downloaded the data."
        )

    logger.info(f"File found: {file_path} ({path_obj.stat().st_size} bytes)")

    # Check readability
    try:
        df = pd.read_parquet(file_path)
        logger.info(f"Successfully read parquet file. Shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Basic sanity check: ensure it's not empty
        if df.empty:
            raise RuntimeError(
                f"CRITICAL: Artifact verification failed. "
                f"File '{file_path}' exists but is empty (0 rows)."
            )
        
        logger.info("Artifact verification PASSED.")
        return True

    except Exception as e:
        raise RuntimeError(
            f"CRITICAL: Artifact verification failed. "
            f"File '{file_path}' exists but could not be read as a valid parquet file. "
            f"Error: {str(e)}"
        )

def main():
    """Entry point for verification."""
    logger.info("Starting artifact verification for T007b...")
    try:
        verify_bronze_parquet()
        logger.info("Verification complete. Ready for T011.")
        sys.exit(0)
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()