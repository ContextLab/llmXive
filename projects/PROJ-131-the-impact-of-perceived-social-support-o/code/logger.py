"""
logger.py
----------
Centralized logging configuration for the project pipeline.

Provides a ``get_logger`` helper that configures a file handler writing to
``data/logs/pipeline.log`` as well as a console handler.  The logger is
configured only once per process to avoid duplicate handlers.
"""

import logging
from pathlib import Path

# Define the directory and file for pipeline logs
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "pipeline.log"

def get_logger(name: str) -> logging.Logger:
    """
    Return a logger with a standard configuration.

    Parameters
    ----------
    name: str
        Name of the logger (typically ``__name__``).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Configure the logger only once (first call)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # Standard log format
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler – captures everything
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler – INFO and above
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
