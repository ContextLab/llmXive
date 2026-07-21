"""
Logging configuration and utilities.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from src.utils.config import get_project_root, get_interim_data_dir

def setup_logger(name: str, log_file: Optional[str] = None, level=logging.INFO) -> logging.Logger:
    """
    Sets up a logger with console and optional file handler.
    
    Args:
        name: Logger name.
        log_file: Relative path to log file (inside interim/).
        level: Logging level.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler if specified
    if log_file:
        log_dir = get_interim_data_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / log_file
        
        fh = logging.FileHandler(log_path)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def get_log_file(filename: str) -> Path:
    """Returns the full path for a log file in the interim directory."""
    return get_interim_data_dir() / filename

def clear_logs():
    """Clears all log files in the interim directory."""
    log_dir = get_interim_data_dir()
    if log_dir.exists():
        for f in log_dir.glob('*.log'):
            f.unlink()
