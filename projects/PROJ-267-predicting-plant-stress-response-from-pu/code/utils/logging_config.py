import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from .config import LOG_LEVEL, LOG_PATH, LOG_MAX_BYTES, LOG_BACKUP_COUNT

# Ensure log directory exists
if LOG_PATH:
    LOG_PATH.mkdir(parents=True, exist_ok=True)

_loggers = {}


def setup_logging() -> None:
    """
    Configure the root logger for the application.

    Sets up a rotating file handler for logs and a console handler.
    """
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH, exist_ok=True)

    log_file = LOG_PATH / "pipeline.log"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # Clear existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(LOG_LEVEL)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance.

    Args:
        name: The name of the logger (usually __name__).

    Returns:
        A configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    if not logger.handlers:
        # Ensure root logging is set up
        if not logging.getLogger().handlers:
            setup_logging()
        logger.setLevel(LOG_LEVEL)
        # Handlers are inherited from root, but we ensure propagation is true
        logger.propagate = True
    _loggers[name] = logger
    return logger


def log_warning(message: str) -> None:
    """
    Log a warning message to the root logger.

    Args:
        message: The warning message to log.
    """
    logging.warning(message)
