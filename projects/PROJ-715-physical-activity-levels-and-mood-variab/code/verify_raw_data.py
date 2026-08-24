import os
import sys
import logging
from pathlib import Path
import pandas as pd
from config import get_path, init_logger

logger = logging.getLogger(__name__)

def verify_bronze_parquet() -> bool:
    """
    Explicitly verify that data/raw/bronze.parquet exists and is readable.
    
    This task (T007b) ensures the artifact produced by T007 is valid.
    It checks:
    1. File existence at the declared path.
    2. File readability (can be loaded by pandas).
    3. Non-empty content (at least one row).
    
    Returns:
        True if verification passes.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or corrupted.
        RuntimeError: If the file cannot be read as a Parquet file.
    """
    # Resolve path using the project's config utility
    path = get_path("data/raw", "bronze.parquet")
    logger.info(f"Verifying artifact: {path}")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Bronze data not found at {path}. Run ingest.py first.")
    
    try:
        # Attempt to load the file to verify it is a valid Parquet
        df = pd.read_parquet(path)
        
        if df.empty:
            raise ValueError(f"Bronze data at {path} is empty. The ingestion process may have failed to extract data.")
        
        logger.info(f"Verification successful: {len(df)} rows loaded from {path}")
        return True
        
    except pd.errors.EmptyDataError:
        raise ValueError(f"Bronze data at {path} is empty or corrupted.")
    except Exception as e:
        raise RuntimeError(f"Failed to read or parse bronze.parquet at {path}: {e}")

def main():
    """Entry point for T007b verification script."""
    init_logger()
    logger.info("Starting Artifact Verification (T007b)")
    
    try:
        verify_bronze_parquet()
        logger.info("Artifact verification PASSED. data/raw/bronze.parquet is valid.")
        return 0
    except Exception as e:
        logger.error(f"Artifact verification FAILED: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())