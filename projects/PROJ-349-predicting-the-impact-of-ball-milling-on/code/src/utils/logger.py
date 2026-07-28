"""
Logging infrastructure for the ball milling impact prediction pipeline.

Provides a centralized logger configuration that:
- Sets up a root logger with configurable level (default: INFO)
- Formats logs with timestamp, level, module, and message
- Writes to both console and a rotating file handler (optional)
- Ensures consistent logging across all pipeline modules
"""

import logging
import os
from pathlib import Path
from typing import Optional, Union

# Project root relative to this file (src/utils -> project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Default log file location
_DEFAULT_LOG_DIR = _PROJECT_ROOT / "logs"
_DEFAULT_LOG_FILE = _DEFAULT_LOG_DIR / "pipeline.log"

# Log format string
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Singleton instance to prevent reconfiguration
_logger: Optional[logging.Logger] = None


def _ensure_log_dir(log_dir: Path) -> None:
    """Create the log directory if it does not exist."""
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)


def get_logger(
    name: Optional[str] = None,
    level: Union[int, str] = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    console: bool = True,
    file: bool = True,
) -> logging.Logger:
    """
    Get or create a configured logger instance.

    This function implements a singleton pattern for the root logger to ensure
    consistent configuration across the pipeline. Subsequent calls with the same
    configuration will return the existing logger.

    Args:
        name: Logger name. If None, returns the root logger.
        level: Logging level (e.g., logging.DEBUG, "INFO", "WARNING").
        log_file: Path to the log file. Defaults to logs/pipeline.log.
        console: If True, add a console handler.
        file: If True, add a file handler (if log_file is provided or default exists).

    Returns:
        A configured logging.Logger instance.

    Example:
        >>> logger = get_logger("src.ingest.materials_project", level="DEBUG")
        >>> logger.info("Starting ingestion...")
    """
    global _logger

    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    # Determine log file path
    if log_file is None:
        _ensure_log_dir(_DEFAULT_LOG_DIR)
        log_file_path = _DEFAULT_LOG_FILE
    else:
        log_file_path = Path(log_file)
        if log_file_path.parent and not log_file_path.parent.exists():
            _ensure_log_dir(log_file_path.parent)

    # If no logger exists, create and configure the root logger
    if _logger is None:
        _logger = logging.getLogger()
        _logger.setLevel(level)
        _logger.handlers = []  # Clear any existing handlers

        # Formatter
        formatter = logging.Formatter(_LOG_FORMAT)

        # Console handler
        if console:
            ch = logging.StreamHandler()
            ch.setLevel(level)
            ch.setFormatter(formatter)
            _logger.addHandler(ch)

        # File handler
        if file and log_file_path:
            # Ensure directory exists
            _ensure_log_dir(log_file_path.parent)
            fh = logging.FileHandler(log_file_path)
            fh.setLevel(level)
            fh.setFormatter(formatter)
            _logger.addHandler(fh)

    # If a specific name is requested, return a child logger
    if name:
        return logging.getLogger(name)

    return _logger


def reset_logger() -> None:
    """
    Reset the logger configuration.

    Use this function to reconfigure the logger (e.g., change log level or file path).
    This clears all handlers and resets the singleton state.
    """
    global _logger
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.setLevel(logging.NOTSET)
    _logger = None


def set_log_level(level: Union[int, str]) -> None:
    """
    Set the global logging level for all handlers.

    Args:
        level: The new logging level (e.g., logging.DEBUG, "WARNING").
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        handler.setLevel(level)


# Convenience function to get a module-specific logger
def get_module_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module with default configuration.

    Args:
        module_name: The module name (usually __name__).

    Returns:
        A configured logger instance for the module.
    """
    return get_logger(name=module_name)


# Initialize default logger on import (optional, can be overridden)
# This ensures a logger is available immediately if imported early
try:
    _default_logger = get_logger()
except Exception:
    # Fail gracefully if initialization issues occur (e.g., permissions)
    pass
