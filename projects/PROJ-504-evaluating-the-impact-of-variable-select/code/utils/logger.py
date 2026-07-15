"""
Logging infrastructure for the research pipeline.

Provides a centralized logger configuration that respects the project's
execution constraints (CI limits, limited CPU/RAM) and ensures consistent
log formatting across all modules.

Features:
- JSON-compatible formatting for structured logging (optional).
- File and console handlers.
- Custom exception formatting with traceback.
- Integration with the project's config for log levels.
"""

import logging
import os
import sys
import traceback
from logging.handlers import RotatingFileHandler
from typing import Optional

# Try to import config; if not available yet (e.g., during early setup),
# use defaults. This prevents circular import issues during initialization.
try:
    from config import get_config
    _CONFIG = get_config()
except Exception:
    _CONFIG = None


DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_DIR = "results/logs"
DEFAULT_LOG_FILE = "pipeline.log"
MAX_LOG_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5


def _get_log_level() -> int:
    """Determine log level from config or environment."""
    if _CONFIG and hasattr(_CONFIG, "log_level"):
        level_str = _CONFIG.log_level
    else:
        level_str = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)
    
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_str.upper(), logging.INFO)


def _ensure_log_dir():
    """Ensure the log directory exists."""
    if _CONFIG and hasattr(_CONFIG, "output_path"):
        log_dir = os.path.join(_CONFIG.output_path, DEFAULT_LOG_DIR)
    else:
        log_dir = DEFAULT_LOG_DIR
    
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def setup_logging(
    name: str = "llmXive",
    level: Optional[int] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger instance with file and console handlers.

    Args:
        name: Name of the logger.
        level: Log level (overrides config/env).
        log_to_file: Whether to write logs to a rotating file.
        log_to_console: Whether to write logs to stdout/stderr.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Prevent adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level or _get_log_level())
    logger.propagate = False

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File Handler
    if log_to_file:
        log_dir = _ensure_log_dir()
        log_path = os.path.join(log_dir, DEFAULT_LOG_FILE)
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=MAX_LOG_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get a logger instance, ensuring it is configured.

    If the logger has no handlers, it will be configured automatically.
    
    Args:
        name: Name of the logger (usually __name__ of the module).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        setup_logging(name=name)
    return logger


def log_exception(logger: logging.Logger, msg: str, exc_info: bool = True):
    """
    Log an exception with full traceback.

    This is a helper to ensure consistent error logging across the pipeline.

    Args:
        logger: The logger instance to use.
        msg: The message to log.
        exc_info: If True, include exception info.
    """
    if exc_info:
        logger.error(msg, exc_info=True)
    else:
        logger.error(msg)
        # Fallback for manual traceback if exc_info is False but we want details
        if sys.exc_info()[0] is not None:
            logger.error("".join(traceback.format_exception(*sys.exc_info())))
