"""
Logging infrastructure for the molecular topology pipeline.

Provides a centralized logging configuration that ensures consistent
log formatting, output, and error handling across all modules.

Features:
- Structured log formatting with timestamps and severity levels.
- Dual output to console and file (configurable).
- Custom exception handling utilities for graceful error reporting.
- Integration with project directory structure for log storage.
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional, Union

# Constants for default log configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_DIR = Path("data/logs")
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class LoggerConfig:
    """Configuration container for logger settings."""

    def __init__(
        self,
        level: int = DEFAULT_LOG_LEVEL,
        log_dir: Optional[Union[str, Path]] = None,
        log_file_name: str = "pipeline.log",
        console_output: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5
    ):
        self.level = level
        self.log_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
        self.log_file_path = self.log_dir / log_file_name
        self.console_output = console_output
        self.max_bytes = max_bytes
        self.backup_count = backup_count


def setup_logger(
    name: str,
    level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = None,
    console: bool = True,
    log_dir: Optional[Union[str, Path]] = None,
    log_file_name: str = "pipeline.log",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up and return a configured logger with optional file rotation.

    This function ensures that loggers are configured only once per process
    to avoid duplicate handlers. It supports both simple file logging and
    rotating file handlers for large log volumes.

    Args:
        name: Name of the logger (usually __name__).
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If provided, overrides log_dir/log_file_name.
        console: If True, also log to console.
        log_dir: Directory to store log files. Defaults to data/logs.
        log_file_name: Name of the log file. Defaults to 'pipeline.log'.
        max_bytes: Maximum size of a log file before rotation (bytes).
        backup_count: Number of backup files to keep.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT
    )

    # Console Handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File Handler
    if log_file:
        log_path = Path(log_file)
    else:
        log_path = Path(log_dir) / log_file_name if log_dir else DEFAULT_LOG_DIR / log_file_name

    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Use RotatingFileHandler for production to prevent disk fill
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def handle_exception(
    logger: logging.Logger,
    exception: Exception,
    message: str = "An unexpected error occurred",
    level: int = logging.ERROR,
    exit_on_error: bool = False
) -> None:
    """
    Log an exception with full traceback and optionally exit the program.

    This utility ensures that all unhandled exceptions are logged consistently
    with their full stack trace, aiding in debugging and audit trails.

    Args:
        logger: The logger instance to use.
        exception: The exception instance to log.
        message: Custom message to include in the log.
        level: Log level for the error (default: ERROR).
        exit_on_error: If True, exit the program with code 1 after logging.
    """
    error_details = f"{message}: {type(exception).__name__}: {str(exception)}"
    logger.log(level, error_details)
    logger.log(level, "Traceback:\n" + traceback.format_exc())

    if exit_on_error:
        logger.critical("FATAL ERROR: Exiting pipeline.")
        sys.exit(1)


def log_critical_failure(
    logger: logging.Logger,
    message: str,
    error_code: int = 1
) -> None:
    """
    Log a critical failure and exit the pipeline.

    This is a specialized helper for scenarios where the pipeline must halt
    immediately due to a critical condition (e.g., insufficient data, validation failure).

    Args:
        logger: The logger instance to use.
        message: Description of the failure.
        error_code: Exit code to return to the OS.
    """
    logger.critical(f"CRITICAL FAILURE: {message}")
    logger.critical(f"Exiting with code {error_code}.")
    sys.exit(error_code)


# Default logger for the package
logger = setup_logger(__name__)