"""
Base logging infrastructure for the llmXive research pipeline.

Provides a centralized logging configuration that ensures consistent
formatting, file rotation, and log levels across all modules.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Union

# Default log level for the application
DEFAULT_LOG_LEVEL = logging.INFO

# Log file name relative to the project root or data directory
DEFAULT_LOG_FILENAME = "pipeline.log"

# Formatter string for log messages
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_logger(
    name: Optional[str] = None,
    log_file: Optional[Union[str, Path]] = None,
    level: int = DEFAULT_LOG_LEVEL,
    console_output: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger instance with file and/or console handlers.

    Args:
        name: Name of the logger. If None, returns the root logger.
        log_file: Path to the log file. If None, no file handler is added.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        console_output: If True, add a console handler.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)

    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add file handler if log_file is provided
    if log_file:
        log_path = Path(log_file)
        # Ensure the directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def configure_root_logger(
    log_file: Optional[Union[str, Path]] = None,
    level: int = DEFAULT_LOG_LEVEL,
) -> logging.Logger:
    """
    Configure the root logger for the entire application.

    Args:
        log_file: Path to the log file.
        level: Logging level.

    Returns:
        The configured root logger.
    """
    return get_logger(
        name=None,
        log_file=log_file,
        level=level,
        console_output=True,
    )


# Convenience function to get a module-specific logger
def get_module_logger(module_name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        module_name: The name of the module (typically __name__).

    Returns:
        A logger instance configured for the module.
    """
    return get_logger(name=module_name)
