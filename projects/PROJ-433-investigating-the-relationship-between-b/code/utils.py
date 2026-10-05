"""
Utility functions for logging, RNG, and QC.
"""
import logging
import os
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

# Configuration
DATA_ROOT = Path("data")
LOG_FILE_PREPROCESS = DATA_ROOT / "preprocess_log.txt"
LOG_FILE_ANALYSIS = DATA_ROOT / "analysis_log.txt"

def setup_logger(name: str = "llmXive", log_file: Optional[Path] = None) -> logging.Logger:
    """
    Set up a logger that writes to both console and a file.

    Args:
        name (str): Logger name.
        log_file (Path, optional): Path to log file. Defaults to preprocess_log.txt.

    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler (if specified, otherwise default)
    if log_file is None:
        log_file = LOG_FILE_PREPROCESS
    
    # Ensure directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def get_seeded_rng(seed: int = 42) -> np.random.Generator:
    """
    Get a numpy random generator with a fixed seed.

    Args:
        seed (int): Random seed.

    Returns:
        np.random.Generator: Seeded random number generator.
    """
    return np.random.default_rng(seed)

def check_fd(fd_value: float, threshold: float = 0.5) -> bool:
    """
    Check if FD value is within acceptable limits.

    Args:
        fd_value (float): Framewise Displacement value.
        threshold (float): Threshold for exclusion.

    Returns:
        bool: True if FD is acceptable (<= threshold), False otherwise.
    """
    return fd_value <= threshold

def log_exclusion(reason: str, subject_id: str) -> None:
    """
    Log an exclusion event.

    Args:
        reason (str): Reason for exclusion.
        subject_id (str): Subject ID.
    """
    logger = setup_logger()
    logger.warning(f"Exclusion logged: {subject_id}, reason: {reason}")
