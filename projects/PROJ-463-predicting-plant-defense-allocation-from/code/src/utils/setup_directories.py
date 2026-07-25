import os
import sys
from pathlib import Path
from typing import List
import logging

from .config import get_data_path
from .logger import get_logger

# Define the required subdirectories for the data hierarchy
REQUIRED_DATA_DIRS: List[str] = [
    "raw",
    "processed",
    "traits",
    "manifests",
    "synthetic"
]

def setup_data_directories(base_path: Path) -> None:
    """
    Create the required directory structure for the plant defense pipeline.
    
    This function ensures that the following directories exist under the base data path:
    - raw: For unaltered downloaded FASTQ files
    - processed: For intermediate and final processed data (trimmed, aligned, TPM)
    - traits: For defense trait data from external sources
    - manifests: For JSON manifests tracking data provenance
    - synthetic: For synthetic data used in prototype validation (NOT raw data)
    
    Args:
        base_path: The root directory where data subdirectories should be created.
                   Typically points to the 'data' directory in the project root.
    """
    logger = get_logger(__name__)
    
    if not base_path.exists():
        logger.info(f"Creating base data directory: {base_path}")
        base_path.mkdir(parents=True, exist_ok=True)
    
    for subdir_name in REQUIRED_DATA_DIRS:
        dir_path = base_path / subdir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory ready: {dir_path}")
        except PermissionError as e:
            logger.error(f"Permission denied creating directory {dir_path}: {e}")
            raise
        except OSError as e:
            logger.error(f"OS error creating directory {dir_path}: {e}")
            raise

def main() -> None:
    """
    CLI entry point for setting up the data directory structure.
    Uses the configured data path from src.utils.config.
    """
    logger = get_logger(__name__)
    logger.info("Starting directory setup for plant defense pipeline...")
    
    try:
        data_path = get_data_path()
        logger.info(f"Target data root: {data_path}")
        
        setup_data_directories(data_path)
        
        # Verify creation
        for subdir_name in REQUIRED_DATA_DIRS:
            dir_path = data_path / subdir_name
            if not dir_path.exists():
                raise RuntimeError(f"Failed to create directory: {dir_path}")
        
        logger.info("Directory structure successfully created.")
        
    except Exception as e:
        logger.critical(f"Directory setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
