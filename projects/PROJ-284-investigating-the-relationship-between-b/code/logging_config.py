import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config import get_config


LOG_DIR = "logs"
LOG_FILE = "pipeline.log"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5


def setup_logging(
    level: Optional[int] = None,
    log_dir: str = LOG_DIR,
    log_file: str = LOG_FILE,
    console: bool = True,
) -> logging.Logger:
    """
    Configure structured logging for the pipeline.

    Creates the log directory if it doesn't exist.
    Configures a rotating file handler and optionally a console handler.
    Returns the root logger with the applied configuration.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
               Defaults to config value or INFO.
        log_dir: Directory path for log files.
        log_file: Name of the log file.
        console: Whether to add a console handler.

    Returns:
        The configured root logger.
    """
    # Ensure log directory exists
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    log_file_path = log_path / log_file

    # Get default level from config if not provided
    if level is None:
        config = get_config()
        level_str = config.get("LOG_LEVEL", "INFO")
        level = getattr(logging, level_str.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on re-calls
    root_logger.handlers.clear()

    # Formatter for structured logging (ISO timestamp, level, name, message)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler with rotation
    try:
        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to simple FileHandler if RotatingFileHandler fails (e.g., permission)
        fallback_handler = logging.FileHandler(log_file_path)
        fallback_handler.setLevel(level)
        fallback_handler.setFormatter(formatter)
        root_logger.addHandler(fallback_handler)
        logging.error(f"RotatingFileHandler failed, using fallback: {e}")

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger with the specified name.

    Args:
        name: Logger name (usually __name__ of the module).

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)
