import logging
import os
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"


def setup_logging(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (optional)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def get_path(subdir: str = "") -> Path:
    """Get a path within the project root."""
    return PROJECT_ROOT / subdir


def get_data_path() -> Path:
    """Get the data directory path."""
    return DATA_DIR


def get_processed_path() -> Path:
    """Get the processed data directory path."""
    return DATA_PROCESSED_DIR


def get_results_path() -> Path:
    """Get the results directory path."""
    return RESULTS_DIR
