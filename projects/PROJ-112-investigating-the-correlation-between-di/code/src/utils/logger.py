import logging
import os
from pathlib import Path
from typing import Optional

# Configuration constants
_LOG_DIR = "data/processed/results/logs"
_LOG_FILE = "pipeline_execution.log"
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global cache to prevent duplicate logger registrations
_logger_cache = {}

def get_logger(name: str, log_dir: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """
    Creates and configures a logger with both console and file handlers.

    Args:
        name: The name of the logger (typically __name__ of the calling module).
        log_dir: Optional override for the log directory (defaults to data/processed/results/logs).
        log_file: Optional override for the log filename (defaults to pipeline_execution.log).

    Returns:
        A configured logging.Logger instance.
    """
    # Determine paths
    if log_dir is None:
        # Resolve relative to project root (assuming code/ is root or parent of src)
        # We use a relative path that works from the project root
        log_dir_path = Path(_LOG_DIR)
    else:
        log_dir_path = Path(log_dir)

    if log_file is None:
        log_file_path = log_dir_path / _LOG_FILE
    else:
        log_file_path = log_dir_path / log_file

    # Ensure log directory exists
    log_dir_path.mkdir(parents=True, exist_ok=True)

    # Return cached logger if it exists
    if name in _logger_cache:
        return _logger_cache[name]

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        _logger_cache[name] = logger
        return logger

    # Formatter
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # File Handler
    file_handler = logging.FileHandler(log_file_path, mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console Handler (INFO level and above for readability)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Cache the logger
    _logger_cache[name] = logger

    return logger

def reset_logger_cache() -> None:
    """
    Clears the logger cache. Useful for testing or re-initialization.
    """
    global _logger_cache
    for name, logger in list(_logger_cache.items()):
        logger.handlers.clear()
        logger.siblings.clear() # type: ignore
    _logger_cache.clear()