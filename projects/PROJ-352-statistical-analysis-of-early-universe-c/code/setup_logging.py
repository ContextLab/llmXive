"""
Logging configuration for the project.

This module provides utilities for setting up logging with
appropriate formatting and file output.
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_dir: Path = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        log_dir: Directory for log files. Defaults to output/logs.
        level: Logging level. Defaults to INFO.

    Returns:
        Configured logger instance.
    """
    if log_dir is None:
        project_root = Path(__file__).resolve().parent.parent
        log_dir = project_root / "output" / "logs"

    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("cmb_analysis")
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"analysis_{timestamp}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def get_logger(name: str = "cmb_analysis") -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name. Defaults to "cmb_analysis".

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)

if __name__ == "__main__":
    # Example usage
    logger = setup_logging()
    logger.info("Logging setup complete.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")