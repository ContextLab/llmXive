import logging
import os
import sys
from pathlib import Path
from typing import Optional
from config.env_config import get_config, get_log_file_path, get_log_level

def setup_logging(log_file: Optional[Path] = None, log_level: Optional[int] = None) -> logging.Logger:
    """
    Configure logging to output to both a file and stdout.
    """
    if log_file is None:
        log_file = get_log_file_path()
    if log_level is None:
        log_level = get_log_level()

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates in re-runs
    logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(log_level)
    fh_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(fh_formatter)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    ch_formatter = logging.Formatter('%(levelname)s: %(message)s')
    ch.setFormatter(ch_formatter)

    # Add handlers
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name, ensuring logging is configured.
    """
    # Ensure global logging is configured
    if not logging.getLogger().handlers:
        setup_logging()
    
    return logging.getLogger(name)

def main():
    """
    Entry point for logging configuration.
    """
    logger = setup_logging()
    logger.info("Logging infrastructure configured.")
    return 0
