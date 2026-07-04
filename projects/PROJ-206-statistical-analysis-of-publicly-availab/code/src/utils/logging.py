"""
Logging infrastructure for the llmXive statistical analysis pipeline.

This module configures a centralized logging system that writes to both
console and a timestamped log file within the project's state directory.
It respects the seed and configuration settings from config.py.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import get_state_root, get_project_root, ensure_dir

# Global logger instance
_logger: Optional[logging.Logger] = None
_initialized: bool = False

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves or creates the project logger.

    Args:
        name: Optional name for the logger. If None, uses the project root name.

    Returns:
        Configured logging.Logger instance.
    """
    global _logger, _initialized

    if not _initialized:
        _setup_logging()

    if name is None:
        # Default to project root name if no name provided
        project_root = get_project_root()
        name = project_root.name if project_root else "llmXive"

    return logging.getLogger(name)

def _setup_logging() -> None:
    """
    Configures the root logger with file and console handlers.
    Ensures log files are written to the state directory.
    """
    global _logger, _initialized

    if _initialized:
        return

    # Ensure state directory exists
    state_root = get_state_root()
    if state_root:
        ensure_dir(state_root)
        log_dir = state_root / "logs"
        ensure_dir(log_dir)
    else:
        # Fallback if state root is not configured yet
        log_dir = Path("state/logs")
        ensure_dir(log_dir)

    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"pipeline_{timestamp}.log"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers to prevent duplicates
    root_logger.handlers.clear()

    # File Handler
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    _initialized = True
    get_logger().info("Logging infrastructure initialized. Log file: %s", log_file)

def set_log_level(level: Union[str, int]) -> None:
    """
    Sets the logging level for the console and file handlers.

    Args:
        level: Logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR') or integer constant.
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setLevel(level)

    get_logger().info("Log level set to %s", logging.getLevelName(level))
