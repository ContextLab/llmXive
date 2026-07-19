"""
Logging Utilities.

Provides a centralized logging configuration.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a logger with file and console handlers.

    Args:
        name: Logger name.
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    # Create logs directory
    log_dir = get_project_root() / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{name}.log"

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def get_logger(name: str) -> logging.Logger:
    """Get or create a logger instance."""
    return setup_logger(name)

def log_exception(e: Exception, logger: Optional[logging.Logger] = None):
    """Log an exception with traceback."""
    if logger is None:
        logger = get_logger(__name__)
    logger.exception(f"Exception occurred: {e}")

def install_global_exception_handler():
    """Install a global exception handler to log uncaught exceptions."""
    def handle_exception(exc_type, exc_value, exc_traceback):
        logger = get_logger(__name__)
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception

def main():
    """Test the logger."""
    logger = get_logger("test_logger")
    logger.info("Test info message")
    logger.error("Test error message")

if __name__ == "__main__":
    main()