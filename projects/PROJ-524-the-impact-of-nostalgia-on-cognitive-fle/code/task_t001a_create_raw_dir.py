"""
Task T001a: Create data/raw/ directory.

This script ensures the existence of the data/raw/ directory structure
required for storing raw input datasets. It uses the project's
configuration and utility modules to handle paths and logging.
"""
import os
import sys
import logging
from pathlib import Path

# Import from project modules as defined in API surface
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning

def create_raw_directory():
    """
    Creates the data/raw/ directory if it does not exist.
    
    Returns:
        Path: The absolute path to the created directory.
        
    Raises:
        RuntimeError: If the directory cannot be created due to permissions or other OS errors.
    """
    config = get_config()
    # Ensure 'data' base directory exists first
    ensure_dirs()
    
    raw_dir = Path(config.get('paths', {}).get('raw_data', 'data/raw'))
    
    if not raw_dir.exists():
        try:
            raw_dir.mkdir(parents=True, exist_ok=True)
            log_info(f"Created directory: {raw_dir}")
        except OSError as e:
            log_error(f"Failed to create directory {raw_dir}: {e}")
            raise RuntimeError(f"Failed to create {raw_dir}") from e
    else:
        log_debug(f"Directory already exists: {raw_dir}")
        
    return raw_dir

def main():
    """Entry point for the script."""
    # Setup logging
    log_level = get_config().get('logging', {}).get('level', 'INFO')
    setup_logging(level=log_level)
    
    try:
        raw_path = create_raw_directory()
        log_info(f"Task T001a completed successfully. Directory: {raw_path}")
        
        # Create a .gitkeep file to ensure the directory is tracked in git
        keep_file = raw_path / ".gitkeep"
        if not keep_file.exists():
            keep_file.write_text("# Placeholder for raw data files\n")
            log_info(f"Created placeholder file: {keep_file}")
            
        return 0
    except Exception as e:
        log_critical(f"Task T001a failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
