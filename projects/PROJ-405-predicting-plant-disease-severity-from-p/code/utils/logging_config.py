"""
Logging infrastructure configuration for the plant disease severity project.

Provides a centralized logging setup that:
1. Configures a structured console logger with colored output (if terminal supports).
2. Configures a rotating file logger for persistent audit trails.
3. Integrates resource usage logging (RAM/CPU) for performance monitoring.
4. Ensures logs are written to `artifacts/logs/` as per project structure.
"""

import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Attempt to import colorama for cross-platform colored logs
try:
    import colorama
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False

from config import get_path

# Constants
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = get_path("artifacts/logs")
LOG_FILE_NAME = "pipeline.log"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ANSI color codes (fallback if colorama not installed)
COLORS = {
    "DEBUG": "\033[36m",      # Cyan
    "INFO": "\033[32m",       # Green
    "WARNING": "\033[33m",    # Yellow
    "ERROR": "\033[31m",      # Red
    "CRITICAL": "\033[35m",   # Magenta
    "RESET": "\033[0m"
}

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds color to log levels in the console."""

    def format(self, record):
        levelname = record.levelname
        color = COLORS.get(levelname, "") if HAS_COLORAMA else ""
        reset = COLORS.get("RESET") if HAS_COLORAMA else ""

        # If colorama is available, init it once
        if HAS_COLORAMA and not colorama.initialized:
            colorama.init()

        if color and reset:
            record.levelname = f"{color}{levelname}{reset}"

        return super().format(record)

def setup_logging() -> logging.Logger:
    """
    Configures the root logger with both console and file handlers.

    Returns:
        logging.Logger: The configured root logger instance.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # Clear existing handlers to avoid duplicates on re-runs
    if root_logger.handlers:
        root_logger.handlers.clear()

    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)

    console_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    if HAS_COLORAMA:
        console_formatter = ColoredFormatter(console_format, datefmt="%Y-%m-%d %H:%M:%S")
    else:
        console_formatter = logging.Formatter(console_format, datefmt="%Y-%m-%d %H:%M:%S")

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # --- File Handler (Rotating) ---
    log_file_path = LOG_DIR / LOG_FILE_NAME
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(LOG_LEVEL)

    # File logs are plain text (no colors) for easier parsing
    file_format = "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(name)s: %(message)s"
    file_formatter = logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Log startup info
    root_logger.info(f"Logging initialized. Level: {LOG_LEVEL}, File: {log_file_path}")

    return root_logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves a logger instance. If name is provided, returns a child logger.
    Otherwise, returns the root logger (already configured by setup_logging).

    Args:
        name (Optional[str]): Module name or custom logger name.

    Returns:
        logging.Logger: The requested logger instance.
    """
    return logging.getLogger(name)

def configure_resource_logging(logger: Optional[logging.Logger] = None):
    """
    Sets up a specific logger for resource usage (RAM, CPU) if needed.
    This is a placeholder for integration with T044/T045 resource monitoring.

    Args:
        logger (Optional[logging.Logger]): The logger to configure. If None, uses root.
    """
    if logger is None:
        logger = logging.getLogger()

    logger.info("Resource logging hooks ready. (Integration with memory tracking pending)")