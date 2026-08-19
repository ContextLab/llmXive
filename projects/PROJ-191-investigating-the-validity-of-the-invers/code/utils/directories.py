import os
import sys
import logging
from pathlib import Path
from typing import List
from config import get_logger, setup_logging

def ensure_data_directories(root_dir: Path) -> List[Path]:
    """
    Ensure that the required data directory structure exists.
    
    This function implements robust 'mkdir -p' logic for the following directories:
    - data/raw/
    - data/processed/
    - data/results/
    
    Args:
        root_dir: The root directory of the project (where 'data' is located).
        
    Returns:
        A list of Path objects for the created/verified directories.
        
    Raises:
        RuntimeError: If a directory cannot be created due to permissions or I/O errors.
    """
    logger = get_logger(__name__)
    
    sub_dirs = [
        "data/raw",
        "data/processed",
        "data/results"
    ]
    
    created_paths = []
    
    for sub_dir in sub_dirs:
        full_path = root_dir / sub_dir
        
        if not full_path.exists():
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
            except PermissionError:
                logger.error(f"Permission denied when creating directory: {full_path}")
                raise RuntimeError(f"Cannot create directory {full_path}: Permission denied")
            except OSError as e:
                logger.error(f"OS error when creating directory {full_path}: {e}")
                raise RuntimeError(f"Cannot create directory {full_path}: {e}")
        else:
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
            logger.debug(f"Directory already exists: {full_path}")
        
        created_paths.append(full_path)
    
    return created_paths

def main():
    """
    Main entry point for ensuring data directories exist.
    
    This script is intended to be run to initialize the data storage structure
    required by the pipeline (T007).
    """
    setup_logging()
    logger = get_logger(__name__)
    
    # Determine project root based on script location
    # Assuming script is at code/utils/directories.py, root is two levels up
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent
    
    logger.info(f"Project root detected at: {project_root}")
    
    try:
        directories = ensure_data_directories(project_root)
        logger.info("Successfully ensured all data directories exist.")
        for d in directories:
            logger.info(f"  - {d}")
        return 0
    except RuntimeError as e:
        logger.error(f"Failed to ensure directories: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
