import logging
import sys
from pathlib import Path
from typing import Optional

# Ensure the log directory exists if we are using a file handler
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Default log file for the project
DEFAULT_LOG_FILE = LOG_DIR / "pipeline.log"

# Format string including timestamp, level, module, and message
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_root_logger: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Returns a configured logger instance.

    This function ensures the root logger is configured only once with:
    1. A StreamHandler writing to stdout for immediate visibility.
    2. A FileHandler writing to data/logs/pipeline.log for persistence.
    3. A consistent formatter including timestamps.

    Args:
        name: The name for the specific logger (e.g., "llmXive.sieve").
            If None or empty, the root logger is returned.

    Returns:
        A configured logging.Logger instance.
    """
    global _root_logger

    if _root_logger is None:
        _root_logger = logging.getLogger("llmXive")
        _root_logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers if this function is called multiple times
        if not _root_logger.handlers:
            # Console Handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(
                logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
            )
            _root_logger.addHandler(console_handler)

            # File Handler
            file_handler = logging.FileHandler(str(DEFAULT_LOG_FILE))
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(
                logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
            )
            _root_logger.addHandler(file_handler)

        # Prevent propagation to the root "root" logger to avoid double logging
        _root_logger.propagate = False

    return logging.getLogger(name)

def set_global_log_level(level: int) -> None:
    """
    Sets the logging level for the entire llmXive logger hierarchy.

    Args:
        level: The logging level (e.g., logging.DEBUG, logging.WARNING).
    """
    global _root_logger
    if _root_logger is None:
        # Initialize if not already done
        get_logger()
    _root_logger.setLevel(level)

    # Update all handlers to match the new level
    for handler in _root_logger.handlers:
        handler.setLevel(level)