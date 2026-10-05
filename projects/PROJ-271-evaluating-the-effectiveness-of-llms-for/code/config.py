import logging
import os
from pathlib import Path
from typing import Optional, Union

# Project root and directory paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"

# Random seed for reproducibility
RANDOM_SEED = 42

# Batch size constraints
LLM_BATCH_SIZE_MAX = 10

def setup_logging(
    name: Optional[Union[str, None]] = None,
    level: Optional[int] = None
) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    This function is designed to be tolerant of various call signatures
    found across the codebase:
    - setup_logging()
    - setup_logging("module_name")
    - setup_logging(__name__)
    - setup_logging("module_name", logging.INFO)
    
    Args:
        name: Optional logger name. If None, returns the root logger.
        level: Optional logging level (e.g., logging.INFO). If None, uses default.
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    if level is not None:
        logger.setLevel(level)
    else:
        logger.setLevel(logging.INFO)
        
    return logger

def get_path(relative_path: str) -> Path:
    """
    Get an absolute path relative to the project root.
    
    Args:
        relative_path: Path relative to project root.
        
    Returns:
        Path: Absolute path.
    """
    return PROJECT_ROOT / relative_path

def get_data_path(filename: str) -> Path:
    """
    Get path to a file in the data directory.
    
    Args:
        filename: Name of the file in data/ directory.
        
    Returns:
        Path: Absolute path to the file.
    """
    return DATA_DIR / filename

def get_processed_path(filename: str) -> Path:
    """
    Get path to a file in the processed data directory.
    
    Args:
        filename: Name of the file in data/processed/ directory.
        
    Returns:
        Path: Absolute path to the file.
    """
    return DATA_PROCESSED_DIR / filename

def get_results_path(filename: str) -> Path:
    """
    Get path to a file in the results directory.
    
    Args:
        filename: Name of the file in results/ directory.
        
    Returns:
        Path: Absolute path to the file.
    """
    return RESULTS_DIR / filename