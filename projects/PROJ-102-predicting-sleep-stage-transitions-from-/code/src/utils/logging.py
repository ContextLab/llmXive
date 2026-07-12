import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from .config import get_paths, get_config

# Default log format
_DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger registry to prevent duplicate handlers
_logger_registry: dict[str, logging.Logger] = {}

def _get_log_dir() -> Path:
    """Retrieve the log directory from the project configuration."""
    paths = get_paths()
    log_dir = paths.log_dir
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def get_log_file_path() -> Path:
    """
    Returns the path to the main project log file.
    Ensures the directory exists.
    """
    log_dir = _get_log_dir()
    return log_dir / "project.log"

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_str: Optional[str] = None,
    date_format: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
) -> None:
    """
    Configures the root logger and the project-specific logger.

    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Path to the log file. Defaults to config log_dir/project.log.
        format_str: Log format string.
        date_format: Date format string.
        enable_console: If True, adds a StreamHandler for stdout.
        enable_file: If True, adds a RotatingFileHandler.
    """
    if format_str is None:
        format_str = _DEFAULT_FORMAT
    if date_format is None:
        date_format = _DEFAULT_DATE_FORMAT
    if log_file is None:
        log_file = get_log_file_path()

    formatter = logging.Formatter(format_str, date_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates if called multiple times
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if enable_file:
        log_dir = log_file.parent
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)

        # Rotate log file: max 10MB, keep 5 backups
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logging.info("Logging infrastructure initialized.")

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves or creates a named logger.
    If setup_logging hasn't been called, it initializes basic logging.
    """
    if name in _logger_registry:
        return _logger_registry[name]

    logger = logging.getLogger(name)

    # If root logger has no handlers, setup basic logging automatically
    if not logging.getLogger().hasHandlers():
        setup_logging()

    _logger_registry[name] = logger
    return logger

def init_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Convenience wrapper for get_logger that ensures the logger is set to the
    specified level and returns it.
    """
    logger = get_logger(name)
    logger.setLevel(level)
    return logger