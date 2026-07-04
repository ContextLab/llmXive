"""
Logging infrastructure for the OSM Urban Heat Island analysis pipeline.
Provides file and stdout handlers with appropriate log levels and formatting.
"""
import logging
import os
from pathlib import Path
from typing import Optional

# Project root relative to this file (assuming code/utils/logging.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "data" / "logs"

# Ensure log directory exists
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instance
_logger: Optional[logging.Logger] = None


def get_logger(name: str = "osm_uhi") -> logging.Logger:
    """
    Retrieves or creates a logger with the specified name.
    Configures file and stdout handlers if not already configured.
    
    Args:
        name: The name for the logger (e.g., 'osm_uhi.ingest')
    
    Returns:
        A configured logging.Logger instance.
    """
    global _logger
    
    # If the specific name logger exists, return it
    # Note: We check the root logger's children or use getLogger directly
    # to ensure we get the hierarchy right.
    logger = logging.getLogger(name)
    
    # If this is the base logger we are configuring, or if it has no handlers yet
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # Formatter for detailed output
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Formatter for console (shorter)
        console_formatter = logging.Formatter(
            '%(levelname)-8s | %(message)s'
        )

        # 1. File Handler (Appends to a timestamped or fixed log file)
        # Using a fixed name 'pipeline.log' for simplicity, could be dynamic
        log_file_path = _LOG_DIR / "pipeline.log"
        try:
            file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            # Fallback if we can't write to disk, log to stderr
            print(f"Warning: Could not create log file at {log_file_path}: {e}", file=__import__('sys').stderr)

        # 2. Console Handler (Stdout)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO) # Only show INFO and above on console by default
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def setup_root_logger() -> logging.Logger:
    """
    Configures the root logger for the application.
    Returns the configured logger.
    """
    return get_logger("osm_uhi")


# Convenience function to get the main application logger
def get_main_logger() -> logging.Logger:
    """
    Returns the main application logger.
    """
    return get_logger("osm_uhi")
