"""
Logging infrastructure for the llmXive research pipeline.

Provides a centralized logging configuration with both file and console handlers.
Ensures consistent log formatting across all project modules.
"""

import logging
import os
from pathlib import Path
from typing import Optional

# Ensure the state directory exists for log files
from src.setup_dirs import setup_directories

_logger: Optional[logging.Logger] = None


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create the project logger with file and console handlers.

    Args:
        name: The name for the logger (default: "llmXive").

    Returns:
        A configured logging.Logger instance.
    """
    global _logger

    if _logger is None:
        # Ensure directories exist before setting up file handlers
        setup_directories()

        # Create the root project logger
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.DEBUG)

        # Avoid adding handlers multiple times if called repeatedly
        if _logger.handlers:
            return _logger

        # Define log format
        log_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(log_format)

        # File Handler
        # Ensure the state directory exists
        state_dir = Path("state")
        if not state_dir.exists():
            state_dir.mkdir(parents=True, exist_ok=True)

        log_file = state_dir / "pipeline.log"
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_format)

        # Add handlers to the logger
        _logger.addHandler(console_handler)
        _logger.addHandler(file_handler)

        # Log initialization
        _logger.info(f"Logger initialized. File logs saved to: {log_file.absolute()}")

    return _logger


def configure_logger(level: int = logging.INFO, name: str = "llmXive") -> logging.Logger:
    """
    Explicitly configure or re-configure the logger.

    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO).
        name: The logger name.

    Returns:
        The configured logger.
    """
    global _logger
    _logger = None  # Reset to force re-initialization
    logger = get_logger(name)
    logger.setLevel(level)
    return logger
