"""
Task T001a: Create data directory: data/raw/

This script ensures the existence of the data/raw/ directory as part of the
project setup phase. It uses the configuration and utility modules to
initialize the logging and directory structure.
"""
import os
import sys
import logging
from pathlib import Path

from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning


def create_raw_directory():
    """
    Creates the 'data/raw/' directory if it does not already exist.

    Returns:
        Path: The path to the created or existing directory.

    Raises:
        OSError: If the directory cannot be created due to permissions or other OS errors.
    """
    config = get_config()
    # Ensure the base data directory exists first
    base_data_dir = Path(config.get('paths', {}).get('data', 'data'))
    ensure_dirs([base_data_dir])

    raw_dir = base_data_dir / 'raw'
    if not raw_dir.exists():
        try:
            raw_dir.mkdir(parents=True, exist_ok=True)
            log_info(f"Created directory: {raw_dir}")
        except OSError as e:
            log_warning(f"Failed to create directory {raw_dir}: {e}")
            raise
    else:
        log_info(f"Directory already exists: {raw_dir}")
    
    return raw_dir


def main():
    """
    Entry point for the T001a task.
    """
    log_level = get_config().get('logging', {}).get('level', 'INFO')
    logger = setup_logging(level=log_level)
    
    try:
        path = create_raw_directory()
        log_info(f"Task T001a completed successfully. Directory: {path}")
        return 0
    except Exception as e:
        log_warning(f"Task T001a failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
