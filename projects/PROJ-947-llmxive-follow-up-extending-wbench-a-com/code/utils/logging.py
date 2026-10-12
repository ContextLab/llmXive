"""
Structured JSON logger utilities for the llmXive project.

Provides a `get_logger` function that returns a logger emitting JSON‑encoded
log records to either stdout or a file. Also supplies convenience wrappers
(`log_info`, `log_error`, `log_warning`, `log_exception`) used throughout
the code base.
"""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

__all__ = [
    "get_logger",
    "log_info",
    "log_warning",
    "log_error",
    "log_exception",
]

class JsonLogFormatter(logging.Formatter):
    """Format LogRecord as a single‑line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        # Base fields
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include any extra context passed via the `extra` argument
        extra = getattr(record, "extra_context", {})
        if isinstance(extra, dict):
            log_entry.update(extra)

        # Ensure JSON is compact and on a single line
        return json.dumps(log_entry, separators=(",", ":"))

def _ensure_handler(logger: logging.Logger, handler: logging.Handler) -> None:
    """Add *handler* to *logger* only if an equivalent handler is not already present."""
    for h in logger.handlers:
        if isinstance(h, type(handler)):
            return
    logger.addHandler(handler)

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger that emits JSON‑formatted logs.

    Parameters
    ----------
    name: str
        Name of the logger (typically ``__name__``).
    log_file: Optional[str]
        If provided, logs are also written to this file (appended).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers on repeated calls
    json_formatter = JsonLogFormatter()

    # StreamHandler to stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(json_formatter)
    _ensure_handler(logger, stream_handler)

    # Optional file handler
    if log_file:
        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setFormatter(json_formatter)
        _ensure_handler(logger, file_handler)

    # Prevent log propagation to the root logger (which could duplicate output)
    logger.propagate = False
    return logger

# Convenience wrappers -----------------------------------------------------

def _log(
    logger: logging.Logger,
    level: int,
    msg: str,
    extra_context: Optional[Dict[str, Any]] = None,
    exc_info: bool = False,
) -> None:
    """
    Internal helper to emit a log record with optional extra context.
    """
    if extra_context is None:
        extra_context = {}
    logger.log(level, msg, extra={"extra_context": extra_context}, exc_info=exc_info)

def log_info(logger: logging.Logger, msg: str, extra_context: Optional[Dict[str, Any]] = None) -> None:
    """Log an INFO‑level message."""
    _log(logger, logging.INFO, msg, extra_context)

def log_warning(logger: logging.Logger, msg: str, extra_context: Optional[Dict[str, Any]] = None) -> None:
    """Log a WARNING‑level message."""
    _log(logger, logging.WARNING, msg, extra_context)

def log_error(logger: logging.Logger, msg: str, extra_context: Optional[Dict[str, Any]] = None) -> None:
    """Log an ERROR‑level message."""
    _log(logger, logging.ERROR, msg, extra_context)

def log_exception(logger: logging.Logger, exc: BaseException, extra_context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an exception with traceback information.

    Parameters
    ----------
    logger: logging.Logger
    exc: BaseException
        The exception instance to log.
    extra_context: Optional[Dict[str, Any]]
        Additional context to include.
    """
    if extra_context is None:
        extra_context = {}
    # Include the exception string in the context
    extra_context["exception"] = str(exc)
    _log(logger, logging.ERROR, f"Exception: {exc}", extra_context, exc_info=True)
