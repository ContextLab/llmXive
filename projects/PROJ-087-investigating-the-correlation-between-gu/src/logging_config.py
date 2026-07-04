import logging
import sys
from typing import Optional

from .config import load_config


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger with a specific format and level.

    This function sets up the logging infrastructure for the project:
    - Configures the root logger to output to stdout.
    - Sets the log format to: '%(asctime)s - %(levelname)s - %(message)s'
    - Sets the default log level to INFO (or the level provided in config).

    Args:
        log_level: Optional string override for the log level (e.g., 'DEBUG', 'WARNING').
                   If None, falls back to the RANDOM_SEED/LOG_LEVEL from config.

    Returns:
        The configured root logger instance.
    """
    # Determine the effective log level
    if log_level is None:
        config = load_config()
        effective_level = config.get("LOG_LEVEL", "INFO")
    else:
        effective_level = log_level.upper()

    # Ensure the level is valid
    try:
        level_value = getattr(logging, effective_level.upper())
    except AttributeError:
        level_value = logging.INFO

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level_value)

    # Remove any existing handlers to prevent duplicates on re-runs
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level_value)

    # Define the formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    # Add the handler to the root logger
    root_logger.addHandler(console_handler)

    return root_logger


# Convenience function to get a logger for a specific module
def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance for the given module name.

    Args:
        name: The name of the module (typically __name__).

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)
