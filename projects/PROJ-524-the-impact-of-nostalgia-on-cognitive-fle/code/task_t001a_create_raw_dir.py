"""
Task T001a: Create data/raw/ directory.

This script creates the `data/raw/` directory required for storing
raw input datasets. It uses the project's configuration and directory
utilities to ensure consistency with the project structure.
"""
import os
import sys
import logging
from pathlib import Path

# Import project utilities
# Note: utils.py is expected to exist based on the API surface provided.
try:
    from utils import setup_logging, log_info, log_warning
except ImportError:
    # Fallback if utils is not yet available (though it should be per T004)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    log_info = logging.info
    log_warning = logging.warning

from config import get_config, ensure_dirs

def create_raw_directory():
    """
    Creates the data/raw/ directory if it does not exist.
    
    Returns:
        Path: The absolute path to the created/existing directory.
    
    Raises:
        RuntimeError: If the directory cannot be created.
    """
    config = get_config()
    base_dir = config.get('base_dir', '.')
    raw_dir_path = Path(base_dir) / 'data' / 'raw'
    
    log_info(f"Ensuring directory exists: {raw_dir_path}")
    
    try:
        # ensure_dirs is a known utility from config.py per API surface
        ensure_dirs([str(raw_dir_path)])
        
        if raw_dir_path.is_dir():
            log_info(f"Successfully ensured directory exists: {raw_dir_path}")
            return raw_dir_path
        else:
            # Fallback manual creation if ensure_dirs didn't work as expected
            raw_dir_path.mkdir(parents=True, exist_ok=True)
            if raw_dir_path.is_dir():
                log_info(f"Successfully created directory: {raw_dir_path}")
                return raw_dir_path
            else:
                raise RuntimeError(f"Failed to create directory: {raw_dir_path}")
                
    except Exception as e:
        log_warning(f"Error ensuring directory {raw_dir_path}: {e}")
        raise RuntimeError(f"Could not create data/raw/ directory: {e}")

def main():
    """Entry point for the task script."""
    setup_logging(level=logging.INFO)
    try:
        path = create_raw_directory()
        log_info(f"T001a COMPLETED: {path}")
        return 0
    except Exception as e:
        log_warning(f"T001a FAILED: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
