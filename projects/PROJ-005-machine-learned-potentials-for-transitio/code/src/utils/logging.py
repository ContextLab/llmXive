"""Utility module for structured JSON logging and progress tracking.

This module provides a simple JSON formatter for the standard ``logging``
library and a thin wrapper around ``tqdm`` to report progress of iterable
processes.  It is deliberately lightweight and has no external runtime
dependencies beyond the optional ``tqdm`` package (which is added to
``requirements.txt``).

Example
-------
>>> from src.utils.logging import get_logger, progress
>>> logger = get_logger(__name__)
>>> for item in progress(range(10), desc="Processing"):
...     logger.info(f"Item {item} processed")
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Iterable, Optional

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    tqdm = None  # type: ignore

__all__ = ["get_logger", "progress"]


class JsonFormatter(logging.Formatter):
    """Format log records as a single‑line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def get_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """
    Return a logger configured with ``JsonFormatter``.

    The function ensures that multiple calls with the same ``name`` do not
    attach duplicate handlers.

    Parameters
    ----------
    name: str
        Name of the logger (typically ``__name__``).
    level: int
        Logging level; defaults to ``logging.INFO``.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return logger


def progress(
    iterable: Iterable[Any],
    desc: str = "",
    total: Optional[int] = None,
    **tqdm_kwargs: Any,
) -> Iterable[Any]:
    """
    Wrap an iterable with ``tqdm`` to display a progress bar.

    Parameters
    ----------
    iterable: Iterable
        The iterable to wrap.
    desc: str, optional
        Description shown next to the progress bar.
    total: int, optional
        Expected length of ``iterable``; if omitted, ``tqdm`` will try to
        infer it.
    **tqdm_kwargs:
        Additional keyword arguments forwarded to ``tqdm``.

    Returns
    -------
    Iterable
        The original iterable wrapped by ``tqdm``.

    Raises
    ------
    ImportError
        If ``tqdm`` is not installed.
    """
    if tqdm is None:
        raise ImportError(
            "tqdm is required for progress tracking. Install it via "
            "'pip install tqdm'."
        )
    return tqdm(iterable, desc=desc, total=total, **tqdm_kwargs)
