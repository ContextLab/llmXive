import logging
import os
import sys
import resource
from pathlib import Path
from logging.handlers import RotatingFileHandler
from utils.config import LOGS, PROJECT_ID

# Ensure logs directory exists
LOGS_PATH = Path(LOGS)
LOGS_PATH.mkdir(parents=True, exist_ok=True)

# Define log file path
LOG_FILE = LOGS_PATH / "pipeline.log"

# Configuration constants
MAX_BYTES = 10 * 1024 * 1024  # 10 MB per file
BACKUP_COUNT = 5              # Keep 5 rotated files
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger instance (initialized lazily)
_logger = None

def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Returns a configured logger instance with both file and console handlers.
    Handles log rotation to prevent disk overflow.
    """
    global _logger
    if _logger is not None and _logger.name == name:
        return _logger

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    # Console handler for stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _logger = logger
    return logger

def log_mode_switch(mode: str, reason: str) -> None:
    """
    Logs a mode switch event (e.g., Primary -> Data Insufficient).
    Uses WARNING level to ensure visibility.
    """
    logger = get_logger()
    logger.warning(f"MODE SWITCH: {mode} | Reason: {reason}")

def log_resource_usage() -> None:
    """
    Logs current CPU and memory usage using the resource module.
    Useful for monitoring pipeline performance and NFR-001 compliance.
    """
    logger = get_logger()
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        max_mem_mb = usage.ru_maxrss / 1024.0  # Convert KB to MB on Linux
        logger.info(f"Resource Usage: Max RSS: {max_mem_mb:.2f} MB, User CPU: {usage.ru_utime:.2f}s, Sys CPU: {usage.ru_stime:.2f}s")
    except Exception as e:
        logger.warning(f"Failed to log resource usage: {e}")

# Initialize the main logger on module load to ensure immediate availability
get_logger()
