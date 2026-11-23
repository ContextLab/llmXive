import logging
import os
import sys
from pathlib import Path
from typing import Optional

from config import get_output_path, get_project_root


def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger to write to a file and stdout.

    Args:
        log_level: The logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional relative path for the log file. Defaults to 'outputs/run.log'.

    Returns:
        The configured root logger instance.
    """
    # Ensure output directory exists
    project_root = get_project_root()
    if log_file:
        log_path = project_root / log_file
    else:
        log_path = get_output_path() / "run.log"

    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates on repeated calls
    if root_logger.handlers:
        root_logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter("%(levelname)s - %(name)s - %(message)s")
    console_handler.setFormatter(console_format)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: The name of the logger (usually __name__).

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)


def main():
    """
    Entry point for testing the logging configuration.
    Writes a test log entry to outputs/run.log.
    """
    setup_logging()
    logger = get_logger("T006")
    logger.info("Logging infrastructure initialized successfully.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")
    print("Log entries written to outputs/run.log")


if __name__ == "__main__":
    main()