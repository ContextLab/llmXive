"""
Utility functions for the llmXive science pipeline.

This module provides logging setup, RNG management, and QC utilities
used across the project.
"""
import logging
import os
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional


def setup_logger(name: str = "llmXive", log_dir: str = "data") -> logging.Logger:
    """
    Configure and return a logger that writes to both preprocess and analysis logs.
    
    Args:
        name: Name of the logger instance.
        log_dir: Directory where log files will be stored.
        
    Returns:
        Configured logging.Logger instance.
        
    The logger writes ISO-timestamped entries to:
        - data/preprocess_log.txt
        - data/analysis_log.txt
    """
    # Ensure log directory exists
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid adding handlers if they already exist (prevents duplicate logs in same process)
    if logger.handlers:
        return logger
    
    logger.handlers.clear()
    
    # Define log file paths
    preprocess_log_file = log_path / "preprocess_log.txt"
    analysis_log_file = log_path / "analysis_log.txt"
    
    # Create file handlers
    fh_preprocess = logging.FileHandler(preprocess_log_file)
    fh_preprocess.setLevel(logging.DEBUG)
    
    fh_analysis = logging.FileHandler(analysis_log_file)
    fh_analysis.setLevel(logging.DEBUG)
    
    # Create formatter with ISO timestamp
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    
    fh_preprocess.setFormatter(formatter)
    fh_analysis.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(fh_preprocess)
    logger.addHandler(fh_analysis)
    
    return logger


def get_seeded_rng(seed: int = 42) -> np.random.Generator:
    """
    Create a numpy random Generator with a fixed seed for reproducibility.
    
    Args:
        seed: Integer seed value for the random number generator.
            
    Returns:
        numpy.random.Generator instance initialized with the seed.
    """
    return np.random.default_rng(seed)


def check_fd(fd_value: float, threshold: float = 0.5) -> bool:
    """
    Check if a Framewise Displacement (FD) value is within acceptable limits.
    
    Args:
        fd_value: The calculated FD value for a subject or time point.
        threshold: The maximum acceptable FD value (default 0.5mm).
            
    Returns:
        True if FD is within acceptable limits (fd_value <= threshold), False otherwise.
    """
    return fd_value <= threshold


def log_exclusion(logger: logging.Logger, reason: str, subject_id: str) -> None:
    """
    Log an exclusion event with the subject ID and reason.
    
    Args:
        logger: The logger instance to use.
        reason: The reason for exclusion (e.g., "FD > 0.5mm").
        subject_id: The ID of the excluded subject.
    """
    logger.warning(f"EXCLUSION | Subject: {subject_id} | Reason: {reason}")
