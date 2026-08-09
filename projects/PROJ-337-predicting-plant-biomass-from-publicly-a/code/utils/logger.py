"""
Logging infrastructure with exclusion rate tracking.

This module provides a centralized logging configuration that:
1. Sets up file and console handlers with appropriate levels.
2. Tracks exclusion counts (e.g., cloud-masked scenes, invalid data) to calculate
   exclusion rates dynamically.
3. Provides a utility to log the final exclusion rate summary.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Optional
import threading

from code.utils.config import get_config

# Thread-local storage for exclusion counters to support concurrent processing
_local = threading.local()


def _get_counters() -> Dict[str, int]:
    """Retrieve or initialize the thread-local exclusion counters."""
    if not hasattr(_local, 'counters'):
        _local.counters = {
            "total_processed": 0,
            "total_excluded": 0,
            "exclusions_by_reason": {}
        }
    return _local.counters


def increment_exclusion(reason: str = "general") -> None:
    """
    Increment the exclusion count for a specific reason.

    Args:
        reason: A string key identifying the reason for exclusion (e.g., 'cloud_cover', 'missing_label').
    """
    counters = _get_counters()
    counters["total_excluded"] += 1
    counters["exclusions_by_reason"][reason] = counters["exclusions_by_reason"].get(reason, 0) + 1


def increment_processed() -> None:
    """Increment the total processed count."""
    counters = _get_counters()
    counters["total_processed"] += 1


def get_exclusion_rate() -> float:
    """
    Calculate the current exclusion rate.

    Returns:
        The ratio of excluded items to total processed items.
        Returns 0.0 if no items have been processed yet.
    """
    counters = _get_counters()
    if counters["total_processed"] == 0:
        return 0.0
    return counters["total_excluded"] / counters["total_processed"]


def reset_counters() -> None:
    """Reset all exclusion and processed counters for the current thread."""
    _local.counters = {
        "total_processed": 0,
        "total_excluded": 0,
        "exclusions_by_reason": {}
    }


def log_exclusion_summary(logger: Optional[logging.Logger] = None) -> None:
    """
    Log a summary of exclusion statistics.

    Args:
        logger: The logger instance to use. If None, uses the module's default logger.
    """
    if logger is None:
        logger = get_logger(__name__)

    counters = _get_counters()
    total = counters["total_processed"]
    excluded = counters["total_excluded"]
    rate = get_exclusion_rate()

    logger.info(f"Exclusion Summary: {excluded}/{total} items excluded ({rate:.2%})")
    if counters["exclusions_by_reason"]:
        logger.info("Exclusions by reason:")
        for reason, count in sorted(counters["exclusions_by_reason"].items()):
            logger.info(f"  - {reason}: {count}")


def setup_logging(log_level: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger and return a named logger.

    This sets up:
    - A console handler with a specific format.
    - An optional file handler if a path is provided.
    - Exclusion rate tracking integration via custom log messages.

    Args:
        log_level: String representation of log level (e.g., 'INFO', 'DEBUG').
                   Defaults to 'INFO' if not specified or if config is missing.
        log_file: Relative or absolute path to a log file. If None, only logs to console.

    Returns:
        A configured logger instance.
    """
    # Determine log level
    if log_level is None:
        try:
            config = get_config()
            log_level = config.get("logging", {}).get("level", "INFO")
        except Exception:
            log_level = "INFO"

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates on re-runs in same process
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler (if requested)
    if log_file:
        log_path = Path(log_file)
        # Ensure directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a logger by name.

    Args:
        name: The name of the logger (usually __name__).

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)
