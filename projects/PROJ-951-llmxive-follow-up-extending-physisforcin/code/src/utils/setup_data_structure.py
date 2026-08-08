"""
Setup script for T005: Data directory structure and checksumming utilities.

This script creates the required data directory structure and initializes
the checksumming infrastructure.
"""
import os
import sys
import logging
from pathlib import Path

from src.utils.io_utils import ensure_dirs, validate_project_structure, get_data_stats, update_checksums

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to set up the data directory structure.
    """
    # Determine project root
    # Assuming this script is run from code/ directory
    code_dir = Path(__file__).resolve().parent.parent
    project_root = code_dir.parent
    
    logger.info(f"Project root: {project_root}")
    
    # Define required data directories
    data_dirs = [
        "data/raw",
        "data/curated",
        "data/eval",
        "data/validation",
        "data/control",
        "data/prompts"
    ]
    
    # Create directories
    logger.info("Creating data directory structure...")
    ensure_dirs([project_root / d for d in data_dirs])
    
    # Validate structure
    logger.info("Validating data directory structure...")
    is_valid, missing = validate_project_structure(project_root, data_dirs)
    
    if not is_valid:
        logger.error(f"Missing directories: {missing}")
        sys.exit(1)
    
    logger.info("Data directory structure validated successfully.")
    
    # Initialize checksums for each data directory
    for data_dir in data_dirs:
        dir_path = project_root / data_dir
        checksums_path = dir_path / ".checksums.json"
        
        # Only create checksums file if directory is empty or doesn't exist
        if not checksums_path.exists():
            update_checksums(dir_path, checksums_path)
            logger.info(f"Initialized checksums for {data_dir}")
    
    # Print statistics
    logger.info("Data directory statistics:")
    for data_dir in data_dirs:
        stats = get_data_stats(project_root / data_dir)
        logger.info(f"  {data_dir}: {stats['file_count']} files, {stats['total_size_mb']:.2f} MB")
    
    logger.info("Setup completed successfully.")

if __name__ == "__main__":
    main()