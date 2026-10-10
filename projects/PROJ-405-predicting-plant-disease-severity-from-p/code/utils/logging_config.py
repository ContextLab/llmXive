import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from config import get_path

# Initialize logger instance
_logger_instance: Optional[logging.Logger] = None

class ColoredFormatter(logging.Formatter):
    """Simple colored formatter for console output."""
    grey = "\x1b[38;21m"
    blue = "\x1b[34;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: blue + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Corrected LOG_DIR key – previously used a non‑existent config entry.
LOG_DIR = get_path("artifacts_logs")

def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure root logger with console and file handlers.
    """
    global _logger_instance
    if _logger_instance is not None:
        return  # Already setup

    # Ensure log directory exists
    try:
        log_dir = LOG_DIR
    except KeyError:
        # Fallback if config not fully ready during very early init
        log_dir = Path("artifacts/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "pipeline.log"

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(ColoredFormatter())
    root_logger.addHandler(ch)

    # File Handler
    fh = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(fh)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger by name.
    """
    setup_logging()
    return logging.getLogger(name)

def configure_resource_logging() -> None:
    """
    Additional configuration for resource usage logging if needed.
    Currently handled by the main logging setup.
    """
    pass
