import logging
import sys
from typing import Optional


def configure_root_logger(level: int = logging.INFO, format_string: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger with a specific format and level.

    Args:
        level: The logging level (default: logging.INFO).
        format_string: The log format string. If None, defaults to
                       '%(asctime)s - %(levelname)s - %(message)s'.

    Returns:
        The configured root logger instance.
    """
    if format_string is None:
        format_string = "%(asctime)s - %(levelname)s - %(message)s"

    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates on re-configuration
    if logger.handlers:
        logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(format_string)
    console_handler.setFormatter(formatter)

    # Add handler to the root logger
    logger.addHandler(console_handler)

    return logger


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get or create a named logger, ensuring it is configured with the root logger's settings.

    Args:
        name: The name of the logger (typically __name__).
        level: The logging level for this logger.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # Propagate to root logger which has the handler
    logger.propagate = True
    return logger