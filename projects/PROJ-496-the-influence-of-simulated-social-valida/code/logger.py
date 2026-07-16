"""
Logging infrastructure for the llmXive Research Pipeline.

Provides a centralized logging configuration to ensure consistent
log formatting, levels, and file output across all pipeline stages.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Project root relative to this file (code/ is in projects/PROJ-496/...)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "data" / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instance to avoid re-configuration
_logger_instance: Optional[logging.Logger] = None


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True
) -> None:
    """
    Configure the root logger for the pipeline.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Relative path to log file from project root.
                  Defaults to 'data/logs/pipeline.log'.
        console: If True, logs are also printed to stdout/stderr.
    """
    global _logger_instance

    if _logger_instance is not None:
        # Logger already configured
        return

    # Determine log file path
    if log_file is None:
        log_file = "data/logs/pipeline.log"
    
    full_log_path = PROJECT_ROOT / log_file
    full_log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console Handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(str(full_log_path), mode='a')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Set _logger_instance to root logger for convenience
    _logger_instance = root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger instance.

    If setup_logging() has not been called, it initializes with defaults.

    Args:
        name: Logger name (e.g., 'code.search', 'code.preprocess').
              If None, returns the root logger.

    Returns:
        Configured logging.Logger instance.
    """
    if _logger_instance is None:
        # Initialize with defaults if not explicitly set up
        setup_logging()

    if name is None:
        return logging.getLogger()
    
    return logging.getLogger(name)