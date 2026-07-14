"""
Logging utilities.
"""
import logging
import os
from pathlib import Path
from typing import Optional
from code.config import get_config, ensure_dir

def setup_logger(name: str, log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a logger with file and console handlers.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (optional)
    if log_file:
        ensure_dir(log_file.parent)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return setup_logger(name)

def log_excluded_subjects(logger: logging.Logger, subjects: list, reason: str) -> None:
    """Log excluded subjects."""
    for sub in subjects:
        logger.warning(f"Excluded subject {sub}: {reason}")

def log_feature_filtering(logger: logging.Logger, features: list, reason: str) -> None:
    """Log filtered features."""
    logger.info(f"Filtered {len(features)} features: {reason}")