"""
Logging infrastructure for the llmXive neural oscillations pipeline.

Configures dual output (stdout + file), log rotation to prevent disk overflow,
and captures warnings, mode switches, and resource usage.

FR-008 Compliance:
- Captures warnings, mode switches, and resource usage.
- Outputs to stdout and logs/pipeline.log.
- Configures log rotation (size-based) to prevent disk overflow.
"""
import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Project root path (assumed to be the parent of 'code')
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "pipeline.log"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Constants for log rotation
# Max size: 10MB per file, keep 5 backups to stay well under disk limits
MAX_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5

# Custom log levels for specific pipeline events
# Mode switches (e.g., Data Insufficient, Underpowered)
logging.addLevelName(logging.INFO + 5, "MODE_SWITCH")
logging.INFO_MODE_SWITCH = logging.INFO + 5

# Resource usage warnings (memory, CPU, runtime)
logging.addLevelName(logging.WARNING + 5, "RESOURCE_USAGE")
logging.RESOURCE_USAGE = logging.WARNING + 5


def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Retrieves or creates a logger configured for the pipeline.
    
    Returns a logger with:
    - StreamHandler for stdout (WARNING and above for clean output, INFO for debug)
    - RotatingFileHandler for logs/pipeline.log (INFO and above)
    - Custom format including timestamp, level, and message.
    """
    logger = logging.getLogger(name)
    
    # Prevent adding handlers if already configured (e.g., in tests)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler (stdout)
    # We set level to INFO to capture warnings and mode switches in stdout as well,
    # but keep it clean. If specific debug info is needed, it goes to file.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File Handler (Rotating)
    # This handles the rotation requirement to prevent disk overflow.
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def log_mode_switch(logger: logging.Logger, mode: str, reason: str) -> None:
    """
    Logs a mode switch event (e.g., switching to Data Insufficient mode).
    Uses a custom log level for easy filtering.
    """
    logger.log(logging.INFO_MODE_SWITCH, f"MODE SWITCH: {mode} | Reason: {reason}")


def log_resource_usage(logger: logging.Logger, resource_type: str, value: str, threshold: str = None) -> None:
    """
    Logs resource usage metrics (RAM, CPU, Runtime).
    If a threshold is provided and value exceeds it, logs as WARNING.
    """
    msg = f"RESOURCE USAGE: {resource_type} = {value}"
    if threshold and float(value.replace(',', '').replace('GB', '').replace('MB', '').replace('%', '')) > float(threshold.replace(',', '').replace('GB', '').replace('MB', '').replace('%', '')):
        logger.warning(msg)
    else:
        logger.log(logging.RESOURCE_USAGE, msg)


# Initialize a default logger instance for immediate use if imported
logger = get_logger()
