import os
import sys
import logging
from pathlib import Path
import pandas as pd
from config import get_path, init_logger

logger = init_logger(__name__)

def verify_bronze_parquet():
    """
    Explicitly verify that data/raw/bronze.parquet exists and is readable.
    
    This task implements T007b: Artifact Verification.
    It ensures the file produced by T007 (ingest.py) is present and valid.
    
    Returns:
        bool: True if verification passes, raises RuntimeError otherwise.
    """
    output_path = get_path("data", "raw", "bronze.parquet")
    
    logger.info(f"Verifying artifact: {output_path}")
    
    # 1. Check existence
    if not os.path.exists(output_path):
        raise RuntimeError(
            f"Artifact verification failed: {output_path} does not exist. "
            "Ensure T007 (ingest.py) has run successfully and downloaded the data."
        )
    
    # 2. Check file size (sanity check)
    file_size = os.path.getsize(output_path)
    if file_size == 0:
        raise RuntimeError(
            f"Artifact verification failed: {output_path} exists but is empty (0 bytes)."
        )
    logger.info(f"File size check passed: {file_size} bytes")
    
    # 3. Check readability (try to load)
    try:
        df = pd.read_parquet(output_path)
        logger.info(f"File is readable. Shape: {df.shape}, Columns: {list(df.columns)}")
        
        # Basic sanity check on columns expected by downstream tasks (T011+)
        # The spec implies columns like participant_id, timestamp, step_count
        required_cols = ['participant_id']
        for col in required_cols:
            if col not in df.columns:
                logger.warning(f"Expected column '{col}' not found in bronze.parquet. "
                               "This may cause downstream failures.")
        
        return True
        
    except Exception as e:
        raise RuntimeError(
            f"Artifact verification failed: Could not read {output_path}. "
            f"Error: {str(e)}"
        )

def main():
    """Entry point for verification script."""
    logger.info("Starting artifact verification (T007b)...")
    try:
        success = verify_bronze_parquet()
        if success:
            logger.info("Artifact verification PASSED: data/raw/bronze.parquet is valid.")
            sys.exit(0)
    except RuntimeError as e:
        logger.error(f"Artifact verification FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()