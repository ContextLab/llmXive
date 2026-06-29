"""
Reusable logging utility for the project.

Provides a simple ``get_logger`` function that returns a cached ``logging.Logger``
instance configured with a sensible formatter and a stream handler that writes to
``sys.stdout``.  An optional file handler can be added by passing ``log_file``.
The logger is cached per ``(name, log_file)`` tuple so repeated calls return the
same instance, avoiding duplicate handlers.
"""

import logging
import sys
from typing import Optional, Tuple, Dict

# Internal cache to ensure we return the same logger instance for the same
# ``name``/``log_file`` combination.
_LOGGER_CACHE: Dict[Tuple[str, Optional[str]], logging.Logger] = {}

def _create_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Create and configure a new ``logging.Logger`` instance.

    Parameters
    ----------
    name: str
        Name of the logger (usually ``__name__`` of the calling module).
    level: int, optional
        Logging level to set; defaults to ``logging.INFO``.
    log_file: str, optional
        If provided, a ``FileHandler`` writing to this path is added.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # Prevent log messages from being propagated to the root logger which may
    # have its own handlers (avoids duplicate output).
    logger.propagate = False

    # If the logger already has handlers (e.g., when the function is called
    # multiple times for the same name), we avoid adding duplicates.
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Stream handler (stdout) – always present.
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # Optional file handler.
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

def get_logger(
    name: str = __name__,
    level: Optional[int] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Retrieve a cached logger instance.

    The first call creates the logger via ``_create_logger``; subsequent calls
    return the cached instance.  If ``level`` is supplied it updates the logger's
    level (useful for tests that need to change verbosity).

    Parameters
    ----------
    name: str, optional
        Logger name; defaults to the caller's ``__name__``.
    level: int, optional
        Logging level to set/override.
    log_file: str, optional
        Path to a file for an additional ``FileHandler``.

    Returns
    -------
    logging.Logger
        The requested logger.
    """
    key = (name, log_file)
    if key in _LOGGER_CACHE:
        logger = _LOGGER_CACHE[key]
        if level is not None:
            logger.setLevel(level)
        return logger

    logger = _create_logger(name, level or logging.INFO, log_file)
    _LOGGER_CACHE[key] = logger
    return logger