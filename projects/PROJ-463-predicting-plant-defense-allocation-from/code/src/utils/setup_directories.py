"""
Setup directory structure for the plant defense allocation project.

Creates the required data subdirectories:
- data/raw: For raw FASTQ/SRA downloads
- data/processed: For normalized TPM matrices and corrected data
- data/traits: For defense trait data from TRY/Phenoscape
- data/manifests: For JSON manifests and provenance logs
- data/synthetic: For synthetic data generated for testing
"""
import os
import sys
from pathlib import Path
from .config import get_data_path, get_config
from .logger import get_logger

# Define the required subdirectories relative to the data root
REQUIRED_DIRS = [
    "raw",
    "processed",
    "traits",
    "manifests",
    "synthetic"
]

def setup_data_directories():
    """
    Creates the standard directory structure for data artifacts.
    
    Uses the data path configured in src/utils/config.py.
    Logs creation events and ensures all required subdirectories exist.
    
    Returns:
        Path: The root data directory path
        
    Raises:
        RuntimeError: If directory creation fails
    """
    logger = get_logger("setup_directories")
    config = get_config()
    
    # Get the base data directory from config
    data_root = get_data_path()
    logger.info(f"Setting up data directories under: {data_root}")
    
    # Ensure the base data directory exists
    data_root_path = Path(data_root)
    data_root_path.mkdir(parents=True, exist_ok=True)
    
    created_dirs = []
    failed_dirs = []
    
    for subdir in REQUIRED_DIRS:
        dir_path = data_root_path / subdir
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            logger.debug(f"Created/verified directory: {dir_path}")
        except OSError as e:
            failed_dirs.append(str(dir_path))
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise RuntimeError(f"Failed to create directory {dir_path}: {e}")
    
    if created_dirs:
        logger.info(f"Successfully created/verified {len(created_dirs)} directories")
    if failed_dirs:
        logger.error(f"Failed to create {len(failed_dirs)} directories")
        
    return data_root_path

def main():
    """
    CLI entry point for directory setup.
    
    Can be run as a script: python -m src.utils.setup_directories
    """
    print("Initializing data directory structure...")
    try:
        data_root = setup_data_directories()
        print(f"✓ Data directory structure ready at: {data_root}")
        print(f"  Subdirectories: {', '.join(REQUIRED_DIRS)}")
        return 0
    except Exception as e:
        print(f"✗ Failed to setup directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
