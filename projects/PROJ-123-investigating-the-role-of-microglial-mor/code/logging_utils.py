"""
Logging Utilities.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from code.config import CONFIG, get_project_root

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger


def setup_file_logging(log_path: str) -> None:
    """Setup file logging."""
    logger = logging.getLogger()
    handler = logging.FileHandler(log_path)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)


def warn_missing_metadata(filename: str) -> None:
    """Warn about missing metadata in a file."""
    logger = get_logger(__name__)
    logger.warning(f"WARN-META-001: Missing metadata for file {filename}. Skipping or using defaults.")