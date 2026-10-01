"""
Logging Configuration Module.
Sets up logging to file and console.
"""
import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from .config import LOG_LEVEL, LOG_PATH, LOG_MAX_BYTES, LOG_BACKUP_COUNT

# Fallbacks if config constants are missing or misnamed in config.py
# Note: config.py defines LOG_FILE_PATH, LOGS_PATH, etc.
# We map them here for standard logger setup names if needed, 
# but primarily use the explicit paths from config.
from .config import LOG_FILE_PATH as _log_file_path
from .config import LOGS_PATH as _logs_path

# Define constants if not present in config (defensive)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760")) # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# Ensure log directory exists
_logs_path.mkdir(parents=True, exist_ok=True)

# Global logger instance
_logger = None

def setup_logging():
    """
    Configures the root logger with file and console handlers.
    """
    global _logger

    if _logger is not None:
        return _logger

    logger = logging.getLogger("plant_stress_pipeline")
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    # Prevent duplicate handlers if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # File Handler (Rotating)
    file_handler = RotatingFileHandler(
        _log_file_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _logger = logger
    return logger

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Retrieves a logger, setting up logging infrastructure if not already done.
    """
    setup_logging()
    return logging.getLogger(name)

def log_warning(message: str):
    """
    Convenience function to log a warning.
    """
    setup_logging()
    logging.getLogger().warning(message)
