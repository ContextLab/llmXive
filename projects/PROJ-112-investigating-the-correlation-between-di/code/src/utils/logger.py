import logging
import os
from pathlib import Path
from typing import Optional

# Cache for loggers to prevent re-creation
_logger_cache = {}
_LOG_DIR = "logs"
_LOG_FILE = "pipeline.log"

def reset_logger_cache() -> None:
    """Reset the logger cache. Useful for testing."""
    global _logger_cache
    _logger_cache = {}
    logging.root.handlers = []

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance.
    Creates a file handler and a stream handler if not already created for this name.
    """
    if name in _logger_cache:
        return _logger_cache[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly in same process
    if logger.handlers:
        _logger_cache[name] = logger
        return logger

    # Determine log file path relative to project root
    # Assume this file is in code/src/utils/logger.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    log_dir = project_root / _LOG_DIR
    log_file = log_dir / _LOG_FILE

    log_dir.mkdir(parents=True, exist_ok=True)

    # File Handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)

    # Stream Handler
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    _logger_cache[name] = logger
    return logger
