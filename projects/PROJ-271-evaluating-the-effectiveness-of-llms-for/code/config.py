import logging
import os
from pathlib import Path
from typing import Optional

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"

# Configuration Constants
RANDOM_SEED = 42
BATCH_SIZE = 10
MAX_BATCH_SIZE = 10  # Explicit constraint for FR-008
MAX_RUNTIME_HOURS = 6

# Logging Configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO

def setup_logging(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(LOG_LEVEL)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger

def get_path(relative_path: str) -> Path:
    """Get absolute path relative to project root."""
    return PROJECT_ROOT / relative_path

def get_data_path() -> Path:
    """Get path to data directory."""
    return DATA_DIR

def get_processed_path() -> Path:
    """Get path to processed data directory."""
    return DATA_PROCESSED_DIR

def get_results_path() -> Path:
    """Get path to results directory."""
    return RESULTS_DIR