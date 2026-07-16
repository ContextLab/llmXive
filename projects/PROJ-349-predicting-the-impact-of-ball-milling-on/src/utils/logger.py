"""
Logging infrastructure for the Ball Milling PSD Prediction project.

Provides a centralized logging configuration that supports:
- Console and file output
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Consistent formatting across the application
- Environment variable override for log level

Usage:
    from src.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Starting process...")
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Project root directory (assuming src/utils is two levels deep)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

# Default configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Environment variable to override log level
LOG_LEVEL_ENV_VAR = "BALL_MILLING_LOG_LEVEL"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Cache for configured logger to avoid re-configuration
_configured = False


def _get_log_level_from_env() -> int:
    """
    Retrieve log level from environment variable.

    Returns:
        int: Logging level constant (e.g., logging.INFO)

    Raises:
        ValueError: If the environment variable contains an invalid level.
    """
    level_str = os.getenv(LOG_LEVEL_ENV_VAR, "").upper()
    if not level_str:
        return DEFAULT_LOG_LEVEL

    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
        "FATAL": logging.CRITICAL,
    }

    if level_str not in level_map:
        raise ValueError(
            f"Invalid log level '{level_str}' in environment variable "
            f"'{LOG_LEVEL_ENV_VAR}'. Valid values: {list(level_map.keys())}"
        )

    return level_map[level_str]


def _setup_logging(log_level: Optional[int] = None) -> None:
    """
    Configure the root logger with console and file handlers.

    Args:
        log_level: Optional logging level. If None, uses environment variable
                   or defaults to INFO.
    """
    global _configured

    if _configured:
        return

    # Determine effective log level
    if log_level is None:
        try:
            log_level = _get_log_level_from_env()
        except ValueError as e:
            # Fallback to default if env var is invalid
            print(f"Warning: {e}. Using default level: {DEFAULT_LOG_LEVEL}", file=sys.stderr)
            log_level = DEFAULT_LOG_LEVEL

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates in interactive environments
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler (rotating to prevent huge log files)
    log_file = LOGS_DIR / "app.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    This function ensures the logging infrastructure is set up before
    returning the logger.

    Args:
        name: The name of the logger (typically __name__).

    Returns:
        logging.Logger: A configured logger instance.
    """
    _setup_logging()
    return logging.getLogger(name)


def set_log_level(level: int) -> None:
    """
    Dynamically set the log level for all handlers.

    Args:
        level: The new logging level (e.g., logging.DEBUG).
    """
    _setup_logging(level)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        handler.setLevel(level)
