"""
Logging infrastructure for the plant pathogen host range prediction pipeline.

This module initializes the logging system using Loguru, ensuring:
1. Logs are written to `logs/pipeline.log` with timestamps.
2. Logs propagate to subprocesses (handled by standard stream configuration).
3. Consistent formatting across the application.

FR-010: Logging infrastructure must be implemented.
SC-005: Logs must include timestamps and propagate to subprocesses.
"""

import os
import sys
from pathlib import Path
from loguru import logger
from typing import Optional

# Ensure the logs directory exists
LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE_PATH = LOGS_DIR / "pipeline.log"

def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None) -> None:
    """
    Configure the global logger instance.

    This function:
    1. Removes the default Loguru handler.
    2. Adds a file handler writing to `logs/pipeline.log`.
    3. Adds a console handler for immediate feedback during development.
    4. Configures the format to include timestamps, log level, and message.

    Args:
        log_level: The minimum log level to capture (e.g., "DEBUG", "INFO", "WARNING", "ERROR").
        log_file: Optional custom path for the log file. Defaults to `logs/pipeline.log`.
    """
    # Remove default handler
    logger.remove()

    # Determine log file path
    if log_file is None:
        log_file = LOG_FILE_PATH
    
    # Ensure parent directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Format string with timestamp
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # Add file handler
    logger.add(
        log_file,
        format=log_format,
        level=log_level,
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        enqueue=True,  # Ensures safe logging from multiple processes
    )

    # Add console handler for immediate visibility
    logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
    )

    logger.info(f"Logging initialized. Output file: {log_file}")


def get_logger(name: Optional[str] = None) -> logger.__class__:
    """
    Retrieve the configured logger instance.

    In Loguru, the 'logger' object is a singleton instance. Calling this
    function returns the same configured logger used throughout the application.
    This ensures consistent formatting and propagation settings.

    Args:
        name: Optional name for the logger (Loguru uses a single instance, so this is for compatibility).

    Returns:
        The configured Loguru logger instance.
    """
    return logger


# Initialize logging immediately upon import to ensure it's ready for other modules
# This satisfies the requirement that logs are initialized early in the pipeline.
setup_logging()
