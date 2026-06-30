"""
Logging configuration and utilities.

This module provides utilities for setting up and managing logging within the
llmXive pipeline, ensuring consistent formatting and output destinations.
"""

import logging
import sys
import os

def setup_logging(level: int = logging.INFO) -> None:
    """
    Configures the root logger for the application.

    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO).
    """
    # Prevent duplicate handlers if called multiple times
    if logging.getLogger().handlers:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)

    # Also configure the specific package logger if needed
    package_logger = logging.getLogger("llmXive")
    package_logger.setLevel(level)

# Initialize default logging on import if not already configured
# This is safe because setup_logging checks for existing handlers
setup_logging()

__all__ = ["setup_logging"]