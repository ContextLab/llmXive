"""
Module to set up the required data directory structure.
Creates 'raw' and 'processed' subdirectories under 'code/data/'.
"""
import os
from pathlib import Path
from code.config import ensure_dirs
from code.utils.logging import get_logger

def setup_data_directories() -> None:
    """
    Creates the directory structure for data storage:
    - code/data/raw/
    - code/data/processed/

    Uses the `ensure_dirs` utility from config to guarantee creation.
    Logs the action using the project logger.
    """
    logger = get_logger(__name__)
    
    base_dir = Path("code/data")
    raw_dir = base_dir / "raw"
    processed_dir = base_dir / "processed"
    
    dirs_to_create = [
        base_dir,
        raw_dir,
        processed_dir
    ]
    
    ensure_dirs(dirs_to_create)
    
    logger.info(f"Data directory structure created at: {base_dir}")
    logger.info(f"  - Raw data: {raw_dir}")
    logger.info(f"  - Processed data: {processed_dir}")
    
    # Verify existence
    if not raw_dir.exists() or not processed_dir.exists():
        logger.error("Failed to create required data directories.")
        raise RuntimeError("Data directory setup failed.")
    
    logger.info("Data directory structure verified successfully.")