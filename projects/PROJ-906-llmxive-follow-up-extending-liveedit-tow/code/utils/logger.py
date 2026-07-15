"""
Robust logging infrastructure for the llmXive pipeline.
Handles structured logging, file rotation, and CI-friendly output.
"""
import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Import project config for directory management
# Using relative import logic handled by the runner's sys.path setup
# or direct import if in same package context.
# Since we are in code/utils, we go up one level to code.
try:
    from config import ensure_directories
except ImportError:
    # Fallback for standalone execution or different import context
    def ensure_directories(base: str = "data"):
        os.makedirs(base, exist_ok=True)
        os.makedirs(os.path.join(base, "flow"), exist_ok=True)
        os.makedirs(os.path.join(base, "metrics"), exist_ok=True)

_logger_instance: Optional[logging.Logger] = None


def setup_logging(
    log_dir: str = "data/logs",
    level: int = logging.INFO,
    enable_file: bool = True,
    enable_console: bool = True
) -> logging.Logger:
    """
    Configures the root logger with file and console handlers.
    Ensures log directory exists.

    Args:
        log_dir: Directory to store log files.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        enable_file: Whether to write to a file.
        enable_console: Whether to print to stdout.

    Returns:
        The configured root logger.
    """
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance

    # Ensure log directory exists
    ensure_directories(log_dir)
    # If log_dir is just "data/logs", we might need to create "data" first if it doesn't exist
    base_dir = os.path.dirname(log_dir)
    if base_dir:
        os.makedirs(base_dir, exist_ok=True)

    logger = logging.getLogger("llmXive")
    logger.setLevel(level)
    logger.handlers.clear()  # Clear existing handlers to avoid duplicates

    # Formatter with timestamp and level
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if enable_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"run_{timestamp}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _logger_instance = logger
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves the configured logger instance.
    If not configured yet, initializes with defaults.

    Args:
        name: Optional sub-logger name (e.g., "llmXive.models").

    Returns:
        A logger instance.
    """
    if _logger_instance is None:
        setup_logging()
    
    if name:
        return logging.getLogger(f"llmXive.{name}")
    return _logger_instance
