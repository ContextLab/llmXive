"""
Utility functions for the research pipeline.

This module provides logging configuration and helper functions used
across the data ingestion, matching, aggregation, and modeling modules.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Import config to ensure paths are available
from .config import get_project_root


# Default log format
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger instance cache
_loggers: Dict[str, logging.Logger] = {}


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None,
) -> None:
    """
    Configure the root logger for the pipeline.

    Args:
        level: The logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional relative path to a log file within the project root.
                  If None, only logs to stdout/stderr.
        project_root: Optional Path to the project root. If None, uses config default.

    Returns:
        None
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on re-runs in same process
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        if project_root is None:
            project_root = get_project_root()
        
        # Ensure log directory exists
        log_path = project_root / log_file
        log_dir = log_path.parent
        
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(console_formatter)
        root_logger.addHandler(file_handler)

    # Silence overly verbose third-party libraries if needed
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger, caching it to avoid re-creation.

    Args:
        name: The name of the logger (typically __name__ of the caller).

    Returns:
        A configured logging.Logger instance.
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        # Do not add handlers here; they are managed by setup_logging
        # This ensures the logger inherits the root configuration
        _loggers[name] = logger
    return _loggers[name]