import logging
import sys
from pathlib import Path
from .config import get_project_root, get_output_path
from typing import Optional

_logger_instance: Optional[logging.Logger] = None

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up the global logger instance.

    Args:
        log_level: The logging level to use.
        log_file: Optional path to a log file.

    Returns:
        The configured logger instance.
    """
    global _logger_instance

    if _logger_instance is not None:
        return _logger_instance

    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)

    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    _logger_instance = logger
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve the global logger instance, optionally scoped to a specific module name.

    Args:
        name: Optional module name to retrieve a logger for. If provided,
              ``logging.getLogger(name)`` is returned; otherwise the
              configured global ``llmXive`` logger is returned.

    Returns:
        A ``logging.Logger`` instance.
    """
    global _logger_instance

    # Initialise the logger on first use if it hasn't been set up yet.
    if _logger_instance is None:
        # Use default configuration (INFO level, no file)
        setup_logging()

    if name:
        # Return a logger named after the caller module for clearer log output.
        return logging.getLogger(name)
    return _logger_instance
