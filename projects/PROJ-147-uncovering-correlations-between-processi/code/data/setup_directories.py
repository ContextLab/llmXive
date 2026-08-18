"""
Directory structure setup for data management.

This module ensures the required directory structure for raw and processed
data exists before any data loading or processing operations begin.
"""
import os
from pathlib import Path
from code.config import ensure_dirs
from code.utils.logging import get_logger


def setup_data_directories(base_path: Path) -> None:
    """
    Create the required directory structure for data management.
    
    This function creates the following directory structure under the base path:
    - data/raw/           : For storing original, unmodified data files
    - data/processed/     : For storing cleaned, transformed, and derived data
    
    Args:
        base_path: The root directory where the data folder structure will be created.
                   Typically this is the project root.
    
    Raises:
        OSError: If directories cannot be created due to permissions or other OS issues.
    """
    logger = get_logger(__name__)
    
    # Define the directory structure
    data_dirs = {
        'raw': 'data/raw',
        'processed': 'data/processed'
    }
    
    logger.info("Setting up data directory structure...")
    
    for name, relative_path in data_dirs.items():
        full_path = base_path / relative_path
        ensure_dirs(full_path)
        logger.info(f"Created directory: {full_path}")
    
    logger.info("Data directory structure setup complete.")