"""
Logging infrastructure for the ball milling prediction pipeline.
Provides a centralized logger configuration with level control and file output.
"""
import logging
import os
from pathlib import Path
from typing import Optional, Union

# Global logger instance reference
_logger: Optional[logging.Logger] = None
_handler: Optional[logging.Handler] = None

def get_module_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger instance with standardized configuration.

    Args:
        name: Optional module name for the logger. If None, uses the caller's module name.

    Returns:
        Configured logging.Logger instance.
    """
    global _logger, _handler

    if name is None:
        # Fallback to a default name if not provided
        name = "ball_milling_pipeline"

    # Get the specific logger
    logger = logging.getLogger(name)

    # If the logger already has handlers, return it (prevent duplicate handlers)
    if logger.handlers:
        return logger

    # Configure the logger
    logger.setLevel(logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Also add a file handler if the logs directory exists
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"{name.replace('.', '_')}.log"

    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, IOError) as e:
        # Log warning but don't fail if file logging is unavailable
        logging.warning(f"Could not create file handler for {log_file}: {e}")

    return logger

def set_log_level(level: Union[str, int]) -> None:
    """
    Set the logging level for all handlers in the application.

    Args:
        level: Logging level as string (e.g., 'DEBUG', 'INFO') or integer constant.
    """
    global _logger, _handler

    # Convert string level to integer if necessary
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    # Apply to all existing loggers
    for logger_name in logging.root.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)

    # Update root logger as well
    logging.root.setLevel(level)

def reset_logger() -> None:
    """
    Reset the logger configuration by removing all handlers and closing files.
    Useful for testing or re-initializing logging.
    """
    # Remove all handlers from all loggers
    for logger_name in list(logging.root.manager.loggerDict.keys()):
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()

    # Clear root handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        handler.close()

    # Reset global state
    global _logger, _handler
    _logger = None
    _handler = None