"""
Standardized logging configuration for the llmXive pipeline.

Provides a consistent logging interface across all pipeline components,
writing to both console and file with structured formatting.
"""

import logging
import os
from pathlib import Path
from typing import Optional

# Default configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Project root relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "logs"
_DEFAULT_LOG_FILE = _LOG_DIR / "pipeline.log"

# Global logger registry to prevent duplicate handlers
_registered_loggers = set()


def _ensure_log_dir() -> Path:
    """Ensure the log directory exists."""
    if not _LOG_DIR.exists():
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
    return _LOG_DIR


def get_logger(
    name: Optional[str] = None,
    level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[Path] = None,
    propagate: bool = True,
) -> logging.Logger:
    """
    Retrieve or create a configured logger instance.

    Args:
        name: Logger name (module name if None).
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to log file. Defaults to logs/pipeline.log.
        propagate: Whether to propagate messages to parent loggers.

    Returns:
        Configured logging.Logger instance.
    """
    logger_name = name if name else __name__.split(".")[0]
    logger = logging.getLogger(logger_name)

    # Avoid re-configuring if already configured
    if logger_name in _registered_loggers:
        logger.setLevel(level)
        return logger

    logger.setLevel(level)
    logger.propagate = propagate

    # Clear existing handlers to avoid duplicates in interactive sessions
    if logger.handlers:
        logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if log file is specified or default)
    target_log_file = log_file if log_file else _DEFAULT_LOG_FILE
    try:
        _ensure_log_dir()
        file_handler = logging.FileHandler(target_log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        # Fallback: log warning to console if file logging fails
        console_warning = logging.StreamHandler()
        console_warning.setFormatter(formatter)
        console_warning.setLevel(logging.WARNING)
        # Add a specific handler to warn about file failure without breaking
        # We use a temporary handler to ensure the warning is seen
        warning_msg = f"Failed to initialize file logging at {target_log_file}: {e}"
        print(warning_msg)

    _registered_loggers.add(logger_name)
    return logger


def set_root_level(level: int = DEFAULT_LOG_LEVEL) -> None:
    """Set the logging level for the root logger of this module namespace."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)


def get_log_file_path() -> Path:
    """Return the path to the default log file."""
    _ensure_log_dir()
    return _DEFAULT_LOG_FILE


# Convenience function to get a logger for the current module
def setup_module_logger() -> logging.Logger:
    """
    Setup and return a logger for the module calling this function.
    Automatically detects the caller's module name.
    """
    import inspect
    frame = inspect.currentframe()
    if frame and frame.f_back:
        module_name = frame.f_back.f_globals.get("__name__", "unknown")
    else:
        module_name = "unknown"
    return get_logger(name=module_name)
