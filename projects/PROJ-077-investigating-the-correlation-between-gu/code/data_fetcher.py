"""
Data Fetcher Module: Validates data presence.
"""
import os
import sys
from pathlib import Path
from typing import Optional

from config import INPUT_PATHS, SAMPLE_LIMIT, RANDOM_SEED
from logging_config import get_logger, log_provenance, log_warning, log_pipeline_start, log_pipeline_end

logger = get_logger("data_fetcher")

def fetch_ukbiobank_data() -> None:
    """
    Placeholder for fetching data.
    In a real scenario, this would download from UK Biobank.
    Here, we assume data is already placed in data/raw/
    """
    logger.info("Checking for UK Biobank data...")
    # No actual download implemented here as per task constraints (real data only)
    # We expect the user to have placed the files.
    pass

def check_local_fallback() -> bool:
    """Checks if local data exists."""
    for path in INPUT_PATHS.values():
        if not Path(path).exists():
            return False
    return True

def validate_data() -> bool:
    """
    Validates that data files exist in data/raw/.
    Returns True if all files exist, raises FileNotFoundError otherwise.
    """
    log_pipeline_start("verify_data_source")
    missing = []
    for name, path in INPUT_PATHS.items():
        if not Path(path).exists():
            missing.append(path)
    
    if missing:
        msg = f"Data files missing. Please place UK Biobank data in data/raw/.\nMissing: {missing}"
        log_warning(msg)
        # CRITICAL: Do NOT fallback to synthetic data.
        # Raise an error to stop the pipeline.
        raise FileNotFoundError(msg)
    
    log_pipeline_end("verify_data_source")
    return True

def main():
    """Entry point."""
    try:
        validate_data()
        print("Data validation successful.")
    except FileNotFoundError as e:
        print(f"Data validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
