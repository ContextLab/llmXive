"""
Base logging infrastructure for the Statistical Discrepancies project.
Provides a centralized logging configuration and a factory for named loggers.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# Default log level
DEFAULT_LEVEL = logging.INFO

# Formatter for consistent log output
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

_logger_initialized = False

def setup_logging(
    log_file: Optional[Path] = None,
    level: int = DEFAULT_LEVEL,
    console: bool = True
) -> None:
    """
    Configure the root logger for the project.

    Args:
        log_file: Optional path to a log file. If provided, logs are written there.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        console: If True, also logs to stdout/stderr.
    """
    global _logger_initialized
    if _logger_initialized:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates in re-runs
    root_logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT)

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if log_file:
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    _logger_initialized = True

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger configured with the project's global settings.

    Args:
        name: The name of the logger (usually __name__).

    Returns:
        A configured logging.Logger instance.
    """
    if not _logger_initialized:
        # Auto-initialize if not explicitly set up (useful for quick scripts)
        setup_logging()
    return logging.getLogger(name)
