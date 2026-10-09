"""
Compatibility layer for the original ``utils.logging_config`` API.

Historical pipeline code imports ``setup_logging``, ``get_logger`` and
``log_warning`` from ``code.utils.logging_config``.  The actual
implementation now lives in :pymod:`code.utils.logger`.  This module
re‑exports those callables so that existing imports continue to work
without modification.
"""

from .logger import get_logger as _get_logger
from .logger import log_warning as _log_warning
from .logger import setup_logging as _setup_logging


def setup_logging() -> None:
    """
    Initialise the logging system.

    Delegates to :func:`code.utils.logger.setup_logging`.
    """
    _setup_logging()


def get_logger(name: str = "pipeline"):
    """
    Retrieve the project‑wide logger.

    Parameters
    ----------
    name: str, optional
        Name of the logger to retrieve.  Defaults to ``\"pipeline\"``.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    return _get_logger(name)


def log_warning(message: str) -> None:
    """
    Log a warning message via the shared logger.

    Parameters
    ----------
    message: str
        Warning text.
    """
    _log_warning(message)
