"""
Standardized logging configuration and helpers for the Equivalence Principle pipeline.

Provides:
  - init_logging(): Configure root logger with file and console handlers.
  - get_logger(name): Retrieve a named logger (child of root).
  - log_error, log_warning, log_info, log_progress: Convenience wrappers.

Logs are written to:
  - `data/logs/pipeline.log` (all levels)
  - Console (INFO and above)
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Project root relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "data" / "logs"
_LOG_FILE = _LOG_DIR / "pipeline.log"

# Default log level
_DEFAULT_LEVEL = logging.INFO

# Ensure log directory exists
_LOG_DIR.mkdir(parents=True, exist_ok=True)


class LoggingConfig:
    """Configuration container for logging behavior."""
    level: int = _DEFAULT_LEVEL
    log_file: Path = _LOG_FILE
    log_dir: Path = _LOG_DIR
    console_enabled: bool = True
    file_enabled: bool = True
    format_string: str = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    date_format: str = "%Y-%m-%d %H:%M:%S"


def init_logging(config: Optional[LoggingConfig] = None) -> None:
    """
    Configure the root logger with file and console handlers.

    Args:
        config: Optional LoggingConfig instance. Uses defaults if None.
    """
    if config is None:
        config = LoggingConfig()

    # Ensure directory exists
    config.log_dir.mkdir(parents=True, exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.level)

    # Clear existing handlers to avoid duplicates on re-init
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        fmt=config.format_string,
        datefmt=config.date_format
    )

    # File handler
    if config.file_enabled:
        file_handler = logging.FileHandler(config.log_file, mode='a')
        file_handler.setLevel(config.level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Console handler
    if config.console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a named logger (child of root).

    Args:
        name: Logger name (e.g., 'ingestion', 'estimator').

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


def log_error(message: str, logger_name: str = "root") -> None:
    """Log an error message."""
    logger = get_logger(logger_name)
    logger.error(message)


def log_warning(message: str, logger_name: str = "root") -> None:
    """Log a warning message."""
    logger = get_logger(logger_name)
    logger.warning(message)


def log_info(message: str, logger_name: str = "root") -> None:
    """Log an info message."""
    logger = get_logger(logger_name)
    logger.info(message)


def log_progress(message: str, logger_name: str = "root") -> None:
    """
    Log a progress message (treated as INFO).

    Use this for long-running task updates.
    """
    logger = get_logger(logger_name)
    logger.info(f"[PROGRESS] {message}")


# Initialize logging on module import if not already configured
if not logging.getLogger().handlers:
    init_logging()
