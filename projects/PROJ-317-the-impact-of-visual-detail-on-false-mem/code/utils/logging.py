"""
Logging infrastructure for the Visual Detail and False Memory project.

Configures a centralized logging system that writes to both console and file,
with appropriate formatting and levels for research reproducibility.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Default log directory relative to project root
LOG_DIR = Path("data/logs")
LOG_FILE_NAME = "research.log"
ERROR_LOG_FILE_NAME = "errors.log"

# Default log level
DEFAULT_LEVEL = logging.INFO

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves or creates a logger with the specified name.

    If no name is provided, returns the root logger.
    The root logger is configured to write to both console and file.

    Args:
        name (Optional[str]): Name of the logger. If None, returns root logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    # If this is the root logger or has no handlers, configure it
    if not logger.handlers:
        logger.setLevel(DEFAULT_LEVEL)

        # Create formatters
        detailed_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        simple_formatter = logging.Formatter(
            fmt="%(levelname)s: %(message)s"
        )

        # File handler for general research log
        file_handler = logging.FileHandler(
            LOG_DIR / LOG_FILE_NAME,
            mode='a',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        # Error-specific file handler
        error_handler = logging.FileHandler(
            LOG_DIR / ERROR_LOG_FILE_NAME,
            mode='a',
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)

        # Console handler for interactive use
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        logger.addHandler(console_handler)

        # Prevent propagation to root if this is a child logger
        logger.propagate = False

    return logger

def setup_logging(log_level: Optional[int] = None) -> None:
    """
    Configures the root logger with the specified level.

    This function is typically called once at the entry point of the application.

    Args:
        log_level (Optional[int]): Logging level (e.g., logging.DEBUG, logging.INFO).
                                   If None, uses DEFAULT_LEVEL.
    """
    level = log_level if log_level is not None else DEFAULT_LEVEL
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Ensure handlers are not duplicated if called multiple times
    if not root_logger.handlers:
        detailed_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler = logging.FileHandler(
            LOG_DIR / LOG_FILE_NAME,
            mode='a',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        error_handler = logging.FileHandler(
            LOG_DIR / ERROR_LOG_FILE_NAME,
            mode='a',
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter(fmt="%(levelname)s: %(message)s")
        )

        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(console_handler)

def get_error_logger() -> logging.Logger:
    """
    Returns a specialized logger for error tracking.

    This logger writes only ERROR and CRITICAL messages to the error log file.

    Returns:
        logging.Logger: Logger configured for error reporting.
    """
    return get_logger("error_tracker")

def get_research_logger() -> logging.Logger:
    """
    Returns a specialized logger for research process tracking.

    This logger writes all messages to the main research log.

    Returns:
        logging.Logger: Logger configured for research logging.
    """
    return get_logger("research")

if __name__ == "__main__":
    # Demonstration of logging usage
    setup_logging(logging.DEBUG)
    logger = get_research_logger()
    error_logger = get_error_logger()

    logger.info("Logging infrastructure initialized successfully.")
    logger.debug("This is a debug message for development.")
    logger.warning("This is a warning message.")
    error_logger.error("This is an error message that should go to errors.log.")
    logger.info("Logging demonstration complete.")