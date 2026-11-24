"""
Logging utilities for the project.

This module provides a configurable global logger with both console and file
handlers, as well as a simple decorator to catch and log unhandled exceptions
in functions throughout the codebase.

The logger is created on demand via :func:`get_logger`.  The first call will
configure a logger named ``run_logger`` that writes to ``logs/run.log`` in the
project root and also emits log records to the console (stderr).  Subsequent
calls with the same name will return the already‑configured logger.

Example
-------
>>> from src.utils.logging import get_logger, exception_handler
>>> log = get_logger(__name__)          # obtains a logger for this module
>>> @exception_handler
... def foo():
...     raise ValueError("demo")
>>> foo()                               # logs the exception, returns None
"""

import logging
import sys
from pathlib import Path
from typing import Callable, Any, TypeVar, cast

# Type variable for the decorator wrapper
F = TypeVar("F", bound=Callable[..., Any])

# Default log file location relative to the project root.
# The ``paths`` utility from ``llmxive_toolkit`` is used to create the
# ``logs`` directory safely.
try:
    # ``llmxive_toolkit`` is guaranteed to be on the import path.
    from llmxive_toolkit import paths
except Exception:  # pragma: no cover
    # Fallback: use the current working directory if the toolkit is not
    # available (unlikely in the provided environment).
    paths = None

_DEFAULT_LOG_FILE = Path("logs") / "run.log"


def _ensure_log_dir(log_file: Path) -> None:
    """Make sure the directory for *log_file* exists."""
    log_file.parent.mkdir(parents=True, exist_ok=True)


def get_logger(name: str, log_file: Path | None = None, level: int = logging.INFO) -> logging.Logger:
    """
    Retrieve (or create) a logger with both console and file handlers.

    Parameters
    ----------
    name: str
        Name of the logger, typically ``__name__``.
    log_file: pathlib.Path | None, optional
        Destination file for log records.  If ``None``, defaults to
        ``logs/run.log`` relative to the project root.
    level: int, optional
        Logging level for the logger (default: ``logging.INFO``).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # If the logger already has handlers attached we assume it has been
    # configured previously and simply return it.
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Determine the actual log file path.
    if log_file is None:
        if paths is not None:
            # ``paths`` creates the directory automatically.
            log_path = paths.logs("run.log")  # type: ignore[attr-defined]
        else:
            log_path = _DEFAULT_LOG_FILE
    else:
        log_path = log_file

    _ensure_log_dir(log_path)

    # Formatter shared by all handlers.
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler – writes everything to disk.
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler – writes to stderr.
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Avoid duplicate messages if the root logger also has handlers.
    logger.propagate = False

    logger.debug("Logger '%s' configured with file '%s'", name, log_path)
    return logger


def exception_handler(func: F) -> F:
    """
    Decorator that catches any exception raised by *func*, logs it using the
    module‑level logger, and returns ``None`` instead of propagating the error.

    This is useful for top‑level pipeline steps where a failure should be
    recorded but not crash the entire process.

    Example
    -------
    >>> @exception_handler
    ... def risky():
    ...     raise RuntimeError("boom")
    >>> result = risky()   # result is ``None`` and the traceback is logged.
    """
    logger = get_logger(func.__module__)

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as exc:  # pragma: no cover
            logger.exception("Unhandled exception in %s", func.__name__)
            # Swallow the exception to keep the pipeline running.
            return None

    return cast(F, wrapper)
