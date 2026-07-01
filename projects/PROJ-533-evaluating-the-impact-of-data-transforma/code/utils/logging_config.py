"""
Logging configuration for the research pipeline.

Configures a logger that writes to results/pipeline.log with a specific format
to record exclusions, imputation rates, and transformation interventions.
"""

import logging
import os
from pathlib import Path
from typing import Optional

LOG_FILE = "results/pipeline.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"


def setup_logger(name: str = "research_pipeline", level: int = logging.INFO) -> logging.Logger:
    """
    Set up and return a logger configured to write to results/pipeline.log.

    Args:
        name: Logger name
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Ensure log directory exists
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # Console handler (optional, for immediate feedback)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "research_pipeline") -> logging.Logger:
    """
    Get an existing logger or create a new one with default config.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name, logger.level)
    return logger
