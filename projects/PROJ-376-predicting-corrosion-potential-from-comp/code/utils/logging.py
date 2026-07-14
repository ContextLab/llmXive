"""
Reproducible logging infrastructure for the Corrosion Potential Pipeline.

Implements FR-010:
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Timestamped log entries with ISO 8601 format
- Dual output: console (stdout) and file (data/logs/pipeline.log)
- Consistent formatter across all pipeline components
- Thread-safe logging via standard library handlers
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure log directory exists
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Define log file path
LOG_FILE = LOG_DIR / "pipeline.log"

# Cache to prevent duplicate handlers
_logger_initialized = False


def setup_logger(
    name: str = "corrosion_pipeline",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console_output: bool = True,
) -> logging.Logger:
    """
    Configure and return a reproducible logger instance.

    Args:
        name: Logger name (default: "corrosion_pipeline")
        level: Logging level (default: logging.INFO)
        log_file: Path to log file (default: data/logs/pipeline.log)
        console_output: Whether to log to console (default: True)

    Returns:
        Configured logging.Logger instance
    """
    global _logger_initialized

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Create formatter with ISO 8601 timestamp and level
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # File handler
    file_path = log_file if log_file else LOG_FILE
    try:
        file_handler = logging.FileHandler(file_path, mode="a", encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        # Fallback to console only if file write fails
        sys.stderr.write(f"Warning: Could not create log file {file_path}: {e}\n")

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Mark as initialized to avoid reconfiguration
    _logger_initialized = True

    return logger


def get_logger(name: str = "corrosion_pipeline") -> logging.Logger:
    """
    Retrieve an existing logger or create a new one with default settings.

    Args:
        name: Logger name

    Returns:
        logging.Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name=name)
    return logger


# Convenience function for quick logging without explicit setup
def log_message(
    message: str,
    level: int = logging.INFO,
    logger_name: str = "corrosion_pipeline",
) -> None:
    """
    Log a message using the default logger configuration.

    Args:
        message: Message to log
        level: Logging level
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)
    logger.log(level, message)


# Initialize default logger on import if needed
# This ensures logging is available immediately when module is imported
if not _logger_initialized:
    setup_logger()