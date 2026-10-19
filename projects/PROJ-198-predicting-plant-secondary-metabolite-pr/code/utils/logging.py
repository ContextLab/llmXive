"""
Simple logging utilities used throughout the project.
"""

import logging
from pathlib import Path

_logger = None


def setup_logging(name: str = "pipeline", level: int = logging.INFO, log_file: str = None):
    """
    Configure the root logger.

    Parameters
    ----------
    name : str
        Name of the logger.
    level : int
        Logging level (e.g., logging.INFO).
    log_file : str, optional
        If provided, logs are also written to this file.
    """
    global _logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (optional)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    _logger = logger
    return logger


def get_logger(name: str = __name__):
    """
    Retrieve the configured logger, creating a default one if necessary.
    """
    global _logger
    if _logger is None:
        # Default configuration if ``setup_logging`` has not been called
        setup_logging()
    return logging.getLogger(name)