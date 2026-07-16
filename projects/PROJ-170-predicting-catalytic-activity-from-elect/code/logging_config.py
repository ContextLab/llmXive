import logging
import os
import sys
from pathlib import Path
from typing import Optional

from config import get_output_path, get_project_root


def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure the project's logging infrastructure.

    This function ensures the log directory exists, creates a file handler
    targeting the specified log file (default: 'outputs/run.log'), and
    attaches it to the root logger.

    Args:
        log_file: Relative path from project root to the log file.
                  Defaults to 'outputs/run.log'.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).

    Returns:
        The root logger instance, configured with file and console handlers.
    """
    if log_file is None:
        log_file = "outputs/run.log"

    project_root = get_project_root()
    log_path = project_root / log_file

    # Ensure the directory for the log file exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on re-runs
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Create file handler
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # Create console handler for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger instance.

    If the logging system has not been initialized via setup_logging(),
    this will trigger a default initialization.

    Args:
        name: Name of the logger (typically __name__). If None, returns root logger.

    Returns:
        A configured logger instance.
    """
    if not logging.getLogger().handlers:
        setup_logging()

    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)


def main():
    """
    Entry point for testing the logging configuration.
    Writes a test log entry to outputs/run.log.
    """
    logger = setup_logging()
    logger.info("Logging infrastructure initialized successfully.")
    logger.debug("This is a debug message for T006 verification.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")

    # Verify file existence
    log_path = get_output_path("run.log")
    if log_path.exists():
        logger.info(f"Log file verified at: {log_path}")
    else:
        logger.error("Log file was not created.")


if __name__ == "__main__":
    main()