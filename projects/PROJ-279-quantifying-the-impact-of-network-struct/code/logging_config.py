"""
Logging infrastructure configuration for the llmXive project.

Configures a dual-output logging system:
1. File output to `logs/analysis.log` (INFO level and above)
2. Console output to stdout (INFO level and above)

Provides a pre-configured logger instance for immediate use across the project.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Project root relative to this file (code/ is one level up from root if running from code,
# but typically we assume the script runs from the project root or we resolve relative to __file__)
# To be safe, we resolve the project root as the parent of the 'code' directory.
_CODE_DIR = Path(__file__).parent
_PROJECT_ROOT = _CODE_DIR.parent

# Ensure logs directory exists
_LOGS_DIR = _PROJECT_ROOT / "logs"
_LOG_FILE = _LOGS_DIR / "analysis.log"

# Log format string
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _ensure_log_directory() -> Path:
    """Create the logs directory if it does not exist."""
    if not _LOGS_DIR.exists():
        _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return _LOGS_DIR


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console: bool = True,
    file: bool = True
) -> logging.Logger:
    """
    Configure the root logger for the project.

    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Path to the log file. Defaults to `logs/analysis.log`.
        console: If True, add a StreamHandler for stdout.
        file: If True, add a FileHandler for the log file.

    Returns:
        The configured root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates if called multiple times
    logger.handlers.clear()

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if file:
        if log_file is None:
            log_file = _LOG_FILE
        
        _ensure_log_directory()
        
        # Ensure the log file exists and is writable
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (PermissionError, OSError) as e:
            # Fallback to console only if file logging fails
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            logger.warning(f"Failed to initialize file logging at {log_file}: {e}")

    return logger


# Initialize the logger immediately upon import for convenience
# This ensures that any module importing this file gets a configured logger
# or can use the root logger which is now configured.
setup_logging()

# Convenience alias for the root logger, though standard practice is `logging.getLogger(__name__)`
# in specific modules. This is provided for quick access if needed.
project_logger = logging.getLogger(__name__)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    If name is None, returns the root logger (which is configured).
    Otherwise, returns a child logger that inherits the configuration.
    
    Args:
        name: The name of the logger (e.g., 'code.download').
        
    Returns:
        A configured Logger instance.
    """
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)