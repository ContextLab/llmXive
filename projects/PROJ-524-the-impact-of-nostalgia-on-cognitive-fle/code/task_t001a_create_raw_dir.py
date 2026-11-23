"""
Task T001a: Create data directory: data/raw/

This script creates the 'data/raw' directory if it does not already exist.
It ensures the directory structure required for raw data ingestion is present.
"""
import os
import sys
import logging
from pathlib import Path

from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning

def create_raw_directory():
    """
    Creates the data/raw directory.

    Returns:
        Path: The absolute path to the created directory.

    Raises:
        OSError: If the directory cannot be created due to permissions or other OS errors.
    """
    config = get_config()
    data_root = Path(config.get("data_root", "data"))
    raw_dir = data_root / "raw"

    if raw_dir.exists():
        log_info(f"Directory {raw_dir} already exists.")
        return raw_dir

    try:
        raw_dir.mkdir(parents=True, exist_ok=True)
        log_info(f"Successfully created directory: {raw_dir}")
        return raw_dir
    except OSError as e:
        log_error(f"Failed to create directory {raw_dir}: {e}")
        raise

def main():
    """
    Entry point for Task T001a.
    """
    # Setup logging
    log_level = get_config().get("log_level", "INFO")
    setup_logging(level=log_level)

    log_info("Starting Task T001a: Create data/raw directory")

    try:
        raw_path = create_raw_directory()
        # Verify existence explicitly for the verifier
        if raw_path.is_dir():
            log_info(f"Verification: Directory {raw_path} exists and is a directory.")
            return 0
        else:
            log_error(f"Verification failed: {raw_path} exists but is not a directory.")
            return 1
    except Exception as e:
        log_error(f"Task T001a failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
