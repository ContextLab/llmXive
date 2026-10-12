"""
Minimal logging utilities used across the project.

The functions provide a thin wrapper around the standard ``logging``
module so that other modules can call ``init_logging`` and helper
functions without needing to configure logging themselves.
"""

import logging
from typing import Any, Dict, Optional

_logger = logging.getLogger(__name__)


def init_logging(level: int = logging.INFO) -> None:
    """
    Initialise the root logger with a simple format.

    Parameters
    ----------
    level : int, optional
        Logging level (e.g. ``logging.DEBUG``).  Defaults to INFO.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    _logger.debug("Logging initialized with level %s", logging.getLevelName(level))


def log_exclusion(subject_id: str, reason: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Record an exclusion event.

    Parameters
    ----------
    subject_id : str
        Identifier of the excluded subject.
    reason : str
        Reason for exclusion.
    metadata : dict, optional
        Additional key‑value pairs to log (e.g. ``Mean_FD``).
    """
    msg = f"Exclusion – Subject: {subject_id}, Reason: {reason}"
    if metadata:
        meta_str = ", ".join(f"{k}={v}" for k, v in metadata.items())
        msg += f", {meta_str}"
    _logger.info(msg)


def log_error(message: str) -> None:
    """
    Log an error message.

    Parameters
    ----------
    message : str
        The error description.
    """
    _logger.error(message)


def log_warning(message: str) -> None:
    """
    Log a warning message.

    Parameters
    ----------
    message : str
        The warning description.
    """
    _logger.warning(message)
