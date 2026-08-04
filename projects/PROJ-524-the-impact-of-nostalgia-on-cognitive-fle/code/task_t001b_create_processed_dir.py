import os
import sys
import logging
from pathlib import Path
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning

def create_processed_directory():
    """
    Creates the data/processed/ directory if it does not already exist.
    Returns the Path object of the created directory.
    """
    config = get_config()
    processed_dir = config.get('paths', {}).get('processed', 'data/processed')
    path = Path(processed_dir)
    
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        log_info(f"Created directory: {path}")
    else:
        log_info(f"Directory already exists: {path}")
        
    return path

def main():
    """
    Entry point for the T001b task script.
    """
    logger = setup_logging("T001B")
    log_info("Starting T001b: Create data/processed/ directory")
    
    try:
        create_processed_directory()
        log_info("T001b completed successfully.")
        return 0
    except Exception as e:
        log_error(f"Failed to create directory: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
