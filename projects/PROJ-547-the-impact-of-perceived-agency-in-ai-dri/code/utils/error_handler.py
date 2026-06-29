"""
Utility module for generic error handling across the pipeline.

Provides:
- PipelineError: base custom exception for pipeline‑level errors.
- handle_error: decorator that catches PipelineError (or any Exception), logs
  the error via the central pipeline logger and exits the process with a
  non‑zero status code.
- log_and_exit: helper that logs an error message and exits immediately.
"""

from __future__ import annotations

import sys
from typing import Callable, TypeVar, cast

from logging.pipeline_logger import get_logger

# Generic type for decorator
F = TypeVar("F", bound=Callable[..., object])


class PipelineError(Exception):
    """Base class for all custom pipeline errors."""

    pass


def handle_error(func: F) -> F:
    """
    Decorator that wraps a function with a try/except block.

    If the wrapped function raises ``PipelineError`` (or any other Exception),
    the error is logged using the central ``pipeline_logger`` and the
    interpreter exits with status code ``1``.  The original exception is not
    re‑raised so that the process terminates cleanly.

    Parameters
    ----------
    func: Callable
        Function to be wrapped.

    Returns
    -------
    Callable
        Wrapped function with error handling.
    """

    def wrapper(*args, **kwargs):
        logger = get_logger()
        try:
            return func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            # Log the full exception information
            logger.error(f"Pipeline error in {func.__name__}: {exc}")
            sys.exit(1)

    # Preserve type hints / metadata
    return cast(F, wrapper)


def log_and_exit(message: str, code: int = 1) -> None:
    """
    Log an error message and exit the process with the supplied exit code.

    Parameters
    ----------
    message: str
        Message to be logged.
    code: int, optional
        Exit status code (default is ``1``).
    """
    logger = get_logger()
    logger.error(message)
    sys.exit(code)
