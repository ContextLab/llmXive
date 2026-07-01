"""
Logging configuration for the llmXive project.

Configures a hierarchical logging system that writes to both:
1. A rotating file handler in `logs/`
2. A console handler with colored output (if supported)

Usage:
    import logging
    from logging_config import setup_logging, get_logger
    
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Ready to start analysis.")
"""

import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Import ensure_dirs from config to ensure log directory exists
# We use a dynamic import or direct path resolution to avoid circular dependency issues
# if this file is loaded before config is fully initialized in some contexts.
# However, based on the API surface, config.ensure_dirs is available.
try:
    from config import ensure_dirs
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "project.log"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

# Define a simple formatter
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Console formatter with color codes (optional, fallback to plain)
try:
    import colorama
    colorama.init()
    CONSOLE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    USE_COLOR = True
    LEVEL_COLORS = {
        logging.DEBUG: colorama.Fore.WHITE,
        logging.INFO: colorama.Fore.GREEN,
        logging.WARNING: colorama.Fore.YELLOW,
        logging.ERROR: colorama.Fore.RED,
        logging.CRITICAL: colorama.Fore.RED + colorama.Style.BRIGHT,
    }
except ImportError:
    USE_COLOR = False
    CONSOLE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LEVEL_COLORS = {}

class ColorFormatter(logging.Formatter):
    """Custom formatter that adds color to log levels in the console."""
    
    def format(self, record):
        if USE_COLOR:
            color = LEVEL_COLORS.get(record.levelno, "")
            reset = colorama.Style.RESET_ALL if color else ""
            record.msg = f"{color}{record.msg}{reset}"
        return super().format(record)

def setup_logging(level=logging.INFO):
    """
    Configure the root logger with file and console handlers.
    
    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO).
    """
    # Ensure log directory exists
    if HAS_CONFIG:
        ensure_dirs([LOG_DIR])
    else:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates in interactive environments
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # File Handler (Rotating)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if USE_COLOR:
        console_formatter = ColorFormatter(CONSOLE_FORMAT, DATE_FORMAT)
    else:
        console_formatter = logging.Formatter(CONSOLE_FORMAT, DATE_FORMAT)
        
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: The name of the logger (usually __name__).
    
    Returns:
        A configured logging.Logger instance.
    """
    return logging.getLogger(name)

# Initialize logging immediately if this module is imported directly
if __name__ == "__main__":
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Logging infrastructure initialized successfully.")
    logger.debug("Debug message test.")
    logger.warning("Warning message test.")
    logger.error("Error message test.")
