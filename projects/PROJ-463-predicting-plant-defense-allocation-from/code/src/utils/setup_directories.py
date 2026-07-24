import os
import sys
from pathlib import Path
from .config import get_data_path, get_config
from .logger import get_logger

def setup_data_directories() -> None:
    """
    Create the required directory structure for the project data.
    
    Creates:
    - data/raw: For unaltered fetched FASTQ files from NCBI GEO/SRA
    - data/processed: For processed TPM matrices and analysis results
    - data/traits: For defense trait data from external databases
    - data/manifests: For checksums and provenance records
    - data/synthetic: For structurally valid synthetic data (prototype validation only)
    
    Raises:
        OSError: If directory creation fails
    """
    config = get_config()
    base_path = get_data_path()
    logger = get_logger("setup_directories")
    
    directories = [
        "raw",
        "processed",
        "traits",
        "manifests",
        "synthetic"
    ]
    
    for dir_name in directories:
        dir_path = base_path / dir_name
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            else:
                logger.debug(f"Directory already exists: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise

def main() -> None:
    """CLI entry point for directory setup."""
    setup_data_directories()
    print("Data directory structure setup complete.")
