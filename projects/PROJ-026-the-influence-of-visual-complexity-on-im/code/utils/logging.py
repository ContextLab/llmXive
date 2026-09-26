"""
Logging configuration and utilities.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

from config import get_project_root, ensure_directories


def get_log_path(filename: str = "app.log") -> Path:
    """Get the path to the log file."""
    project_root = get_project_root()
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / filename


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_str: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the project.
    
    Args:
        level: Logging level (default: INFO).
        log_file: Name of the log file (default: app.log).
        format_str: Log format string.
        
    Returns:
        Configured logger.
    """
    if format_str is None:
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
    if log_file is None:
        log_file = "app.log"
        
    log_path = get_log_path(log_file)
    
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers = []
    
    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(level)
    formatter = logging.Formatter(format_str)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


def log_counterbalance_strategy(seed: int, split_ratio: float) -> None:
    """Log the counterbalance strategy used."""
    logger = get_logger(__name__)
    logger.info(f"Counterbalance Strategy: Seed={seed}, Split Ratio={split_ratio:.2f}")