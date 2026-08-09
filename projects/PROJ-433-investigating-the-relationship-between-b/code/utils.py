"""
Utility functions for the Brain Network Dynamics project.
"""
import logging
import os
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

# Configuration
DATA_ROOT = Path("data")
LOG_PREPROCESS = DATA_ROOT / "preprocess_log.txt"
LOG_ANALYSIS = DATA_ROOT / "analysis_log.txt"

def setup_logger(name: str = "pipeline_logger", log_file: Optional[Path] = None) -> logging.Logger:
    """
    Setup a logger that writes to a specific file and console.
    
    Args:
        name: Name of the logger.
        log_file: Path to the log file. If None, defaults to preprocess_log.txt.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    if log_file is None:
        log_file = LOG_PREPROCESS
    
    # Ensure data directory exists
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger
    
    # File handler
    fh = logging.FileHandler(log_file, mode='a')
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter with ISO timestamp
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def get_seeded_rng(seed: int = 42) -> np.random.Generator:
    """
    Create a numpy random generator with a fixed seed for reproducibility.
    
    Args:
        seed: Integer seed for the random number generator.
    
    Returns:
        np.random.Generator: Seeded random number generator.
    """
    return np.random.default_rng(seed)

def check_fd(fd_value: float, threshold: float = 0.5) -> bool:
    """
    Check if a Framewise Displacement (FD) value is within acceptable limits.
    
    Args:
        fd_value: The FD value to check.
        threshold: The maximum allowed FD value (default 0.5mm).
    
    Returns:
        bool: True if FD is acceptable (<= threshold), False otherwise.
    """
    return fd_value <= threshold

def log_exclusion(reason: str, subject_id: str, log_file: Optional[Path] = None) -> None:
    """
    Log an exclusion event for a subject.
    
    Args:
        reason: The reason for exclusion.
        subject_id: The ID of the excluded subject.
        log_file: Path to the log file. If None, defaults to analysis_log.txt.
    """
    if log_file is None:
        log_file = LOG_ANALYSIS
    
    logger = setup_logger(log_file=log_file)
    logger.warning(f"Subject {subject_id} excluded: {reason}")