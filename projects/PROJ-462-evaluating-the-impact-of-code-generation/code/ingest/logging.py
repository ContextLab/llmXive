"""
Logging configuration for ingestion and validation operations.

This module establishes logging infrastructure before implementation of
data ingestion and validation tasks. It provides:
- Configured loggers for ingest and validate components
- File and console handlers
- Appropriate log levels and formatting
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


def _ensure_log_directory() -> Path:
    """
    Ensure the log output directory exists.

    Returns:
        Path to the log directory
    """
    log_dir = Path("data/output")
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_logger(
    name: str = "llmXive.ingest",
    level: int = logging.DEBUG,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Get or create a configured logger for ingestion and validation operations.

    Args:
        name: Logger name (default: "llmXive.ingest")
        level: Minimum log level (default: DEBUG)
        log_to_file: Whether to write logs to file (default: True)
        log_to_console: Whether to write logs to console (default: True)

    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times if logger already configured
    if logger.handlers:
        logger.setLevel(level)
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # Create formatter with timestamp, level, and message
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler for immediate visibility
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler for persistent logs
    if log_to_file:
        log_dir = _ensure_log_directory()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"ingest_{timestamp}.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_ingest_logger() -> logging.Logger:
    """
    Get the logger specifically for data ingestion operations.

    Returns:
        Configured logger for ingestion tasks
    """
    return get_logger("llmXive.ingest.ingest")


def get_validate_logger() -> logging.Logger:
    """
    Get the logger specifically for data validation operations.

    Returns:
        Configured logger for validation tasks
    """
    return get_logger("llmXive.ingest.validate")


def setup_basic_logging(
    log_level: str = "INFO",
    log_dir: Optional[str] = None
) -> None:
    """
    Setup basic logging configuration for the entire ingest module.

    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Optional custom log directory path
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
    else:
        log_path = _ensure_log_directory()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"ingest_{timestamp}.log"

    # Configure root logger for the ingest module
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    # Set propagation to prevent duplicate messages
    logging.getLogger("llmXive").propagate = False


def log_operation_start(
    logger: logging.Logger,
    operation: str,
    **kwargs
) -> None:
    """
    Log the start of an operation with metadata.

    Args:
        logger: Logger instance to use
        operation: Name of the operation
        **kwargs: Additional metadata to log
    """
    metadata = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"Operation '{operation}' started - {metadata}")


def log_operation_end(
    logger: logging.Logger,
    operation: str,
    success: bool = True,
    **kwargs
) -> None:
    """
    Log the end of an operation with status.

    Args:
        logger: Logger instance to use
        operation: Name of the operation
        success: Whether the operation succeeded
        **kwargs: Additional metadata to log
    """
    status = "completed" if success else "failed"
    metadata = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    if metadata:
        logger.info(f"Operation '{operation}' {status} - {metadata}")
    else:
        logger.info(f"Operation '{operation}' {status}")


def log_validation_result(
    logger: logging.Logger,
    check_name: str,
    passed: bool,
    details: Optional[str] = None
) -> None:
    """
    Log a validation check result.

    Args:
        logger: Logger instance to use
        check_name: Name of the validation check
        passed: Whether the check passed
        details: Optional details about the check
    """
    status = "PASSED" if passed else "FAILED"
    message = f"Validation '{check_name}': {status}"
    if details:
        message += f" - {details}"

    if passed:
        logger.debug(message)
    else:
        logger.error(message)