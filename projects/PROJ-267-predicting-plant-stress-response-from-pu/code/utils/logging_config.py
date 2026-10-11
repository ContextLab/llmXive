"""
Logging configuration utilities for the project.

Provides a simple wrapper around the standard ``logging`` module that writes
INFO and WARNING level messages to ``logs/pipeline.log``. All pipeline
modules import :func:`get_logger` from this module, ensuring a single
source of truth for log handling.
"""
import logging
from pathlib import Path

from .config import LOG_PATH, LOG_LEVEL, LOG_MAX_BYTES, LOG_BACKUP_COUNT

# Ensure the logs directory exists at import time – this is safe because the
# path is a simple constant and the operation is idempotent.
LOG_PATH.mkdir(parents=True, exist_ok=True)

_loggers = {}

def _configure_root_logger() -> None:
    """
    Configure the root logger with a rotating file handler that writes to
    ``logs/pipeline.log``. This function is idempotent; calling it multiple
    times has no adverse effect.
    """
    root = logging.getLogger()
    if root.handlers:
        # Assume configuration has already been performed.
        return

    root.setLevel(LOG_LEVEL.upper())

    # Rotating file handler – limits size and keeps a few backups.
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_PATH / "pipeline.log",
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Also output to stdout for immediate feedback during interactive runs.
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

def setup_logging() -> None:
    """
    Public entry point used by the pipeline to initialise logging.
    It simply forwards to ``_configure_root_logger``.
    """
    _configure_root_logger()

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Retrieve a named logger. The first call creates and configures the
    underlying logging system; subsequent calls return the cached logger.

    Args:
        name: Name of the logger (typically ``__name__``).

    Returns:
        A ``logging.Logger`` instance.
    """
    if name in _loggers:
        return _loggers[name]

    # Ensure the root logger is configured before creating child loggers.
    _configure_root_logger()
    logger = logging.getLogger(name)
    _loggers[name] = logger
    return logger

def log_warning(message: str) -> None:
    """
    Convenience helper used by a few legacy modules that previously
    imported ``log_warning`` directly from ``utils.logging_config``.
    """
    get_logger(__name__).warning(message)
