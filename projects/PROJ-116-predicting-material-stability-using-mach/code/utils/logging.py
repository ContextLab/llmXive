import logging
import os
from pathlib import Path
from config import OUTPUTS_LOGS_DIR, LOG_LEVEL, LOG_FILE

_loggers = {}

def setup_logger(name: str, level: int = LOG_LEVEL) -> logging.Logger:
    """
    Sets up a logger with file and console handlers.
    Returns a logger instance, reusing it if it already exists.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Clear existing handlers to avoid duplicates if called multiple times
    logger.handlers.clear()

    # File handler
    OUTPUTS_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(level)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _loggers[name] = logger
    return logger