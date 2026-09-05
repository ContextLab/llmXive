"""
Directory initialization utilities.
"""
import os
import sys
from pathlib import Path
import logging
from utils.logging_config import get_logger

# Project root
project_root = Path(__file__).resolve().parent.parent

# Define required directories
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/figures",
    "logs",
    "code/ingest",
    "code/analysis",
    "code/theory",
    "code/validation",
    "code/utils",
    "code/models",
    "tests/unit",
    "tests/contract",
    "tests/integration"
]

logger = get_logger(__name__)


def initialize_directories() -> None:
    """
    Create all required directories if they do not exist.
    """
    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory ensured: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise


def get_data_dir(subdir: Optional[str] = None) -> Path:
    """
    Get the path to the data directory.
    
    Args:
        subdir: Optional subdirectory within data/.
        
    Returns:
        Path: The full path to the data directory.
    """
    data_dir = project_root / "data"
    if subdir:
        return data_dir / subdir
    return data_dir


def get_raw_data_dir() -> Path:
    """
    Get the path to the raw data directory.
    
    Returns:
        Path: The full path to data/raw.
    """
    return get_data_dir("raw")


def get_processed_data_dir() -> Path:
    """
    Get the path to the processed data directory.
    
    Returns:
        Path: The full path to data/processed.
    """
    return get_data_dir("processed")
