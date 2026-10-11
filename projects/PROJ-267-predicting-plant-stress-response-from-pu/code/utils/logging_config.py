"""
Compatibility wrapper for logging configuration.

This module provides the same public functions that were previously
defined in the original ``utils.logging_config`` module, but all of them
now delegate to the project‑wide logger implementation in
``utils.logger``.  By centralising the logger creation here we guarantee
that every pipeline component that imports ``get_logger`` (or the helper
``setup_logging`` / ``log_warning``) uses the single logger that writes to
`logs/pipeline.log`.
"""

from .logger import get_logger as _get_logger

__all__ = [
    "get_logger",
    "setup_logging",
    "log_warning",
]

def get_logger(name: str = __name__):
    """
    Return the shared project logger.

    This is a thin wrapper around ``utils.logger.get_logger`` so that
    existing import statements (e.g. ``from utils.logging_config import
    get_logger``) continue to work without modification.
    """
    return _get_logger(name)

def setup_logging(log_file=None, log_level=None):
    """
    Initialise logging for a script.

    The underlying logger is already configured to write to
    ``logs/pipeline.log``; this helper simply returns that logger and,
    optionally, adjusts its level.
    """
    logger = _get_logger()
    if log_level is not None:
        logger.setLevel(log_level)
    # ``log_file`` is ignored because the logger always writes to the
    # canonical pipeline log file defined in ``utils.logger``.
    return logger

def log_warning(message: str):
    """
    Convenience wrapper used by older modules.

    Logs a warning message using the shared project logger.
    """
    logger = _get_logger()
    logger.warning(message)
