import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional

# Define the log directory relative to project root
# Assuming project root is two levels up from code/utils
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = PROJECT_ROOT / "state" / "logs"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger registry to enforce singleton per name
_loggers: dict[str, logging.Logger] = {}

def setup_root_logger(level: int = logging.INFO) -> logging.Logger:
    """
    Configures the root logger with a rotating file handler and a console handler.
    This should be called once at the start of the application.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on re-runs in same process
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Create log file path with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = LOG_DIR / f"project_{timestamp}.log"

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(file_formatter)
    root_logger.addHandler(console_handler)

    return root_logger

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Retrieves or creates a named logger.
    Ensures the root logger is configured if this is the first call.
    Returns a singleton logger instance per name.
    """
    if not _loggers:
        # Initialize root logger on first request if not already done
        setup_root_logger()

    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent propagation to root to avoid double logging if root is also configured
    # However, usually we want propagation if root is set up, but since we are
    # adding handlers to root in setup_root_logger, we might double log if not careful.
    # Standard practice: Add handlers to root, set propagate=True (default).
    # But here we are managing a custom setup. Let's ensure we don't add duplicate handlers
    # to the specific logger if it's a child of root.
    
    # Since setup_root_logger adds handlers to root, and we want this logger to use them:
    logger.propagate = True
    
    _loggers[name] = logger
    return logger
