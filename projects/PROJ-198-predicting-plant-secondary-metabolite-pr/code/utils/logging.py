"""
Minimal logging utilities used throughout the project.
"""
import logging
import sys
from pathlib import Path

_loggers = {}

def setup_logging(name: str = "pipeline", level: int = logging.INFO, log_file: str | None = None) -> None:
    """Configure root logger with console and optional file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Optional file handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

def get_logger(name: str) -> logging.Logger:
    """Retrieve a named logger, creating it if necessary."""
    if name not in _loggers:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        _loggers[name] = logger
    return _loggers[name]