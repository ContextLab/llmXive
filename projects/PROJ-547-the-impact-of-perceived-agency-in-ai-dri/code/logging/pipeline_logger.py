"""
Centralized logging infrastructure for the project.

Provides a singleton logger that writes log records as JSON lines to a
timestamped file under the ``logs/`` directory.

Usage
-----
>>> from pipeline_logger import get_logger
>>> logger = get_logger()
>>> logger.info("Processing started", extra={"step": "ingest"})
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

__all__ = ["get_logger", "log_dict"]

_LOGGER_NAME = "pipeline"
_LOGGER: logging.Logger | None = None


class _JSONFormatter(logging.Formatter):
    """
    Formatter that serialises a LogRecord to a single JSON object per line.

    The JSON object contains:

    - ``timestamp``: ISO‑8601 UTC timestamp with ``Z`` suffix.
    - ``level``: Log level name (e.g. ``INFO``).
    - ``message``: The rendered log message.
    - Any user‑supplied ``extra`` fields passed to ``logger.log``.
    """

    # Default attributes that the logging module adds to a LogRecord.
    _DEFAULT_ATTRS = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:
        # Base fields
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Include any user‑supplied ``extra`` attributes.
        for key, value in record.__dict__.items():
            if key not in self._DEFAULT_ATTRS and not key.startswith("_"):
                log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False)

def _create_file_handler() -> logging.FileHandler:
    """Create a ``FileHandler`` that writes JSON lines to a timestamped file."""
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"run_{timestamp}.log"

    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(_JSONFormatter())
    return file_handler

def get_logger(name: str = _LOGGER_NAME) -> logging.Logger:
    """
    Return the singleton pipeline logger.

    The logger writes JSON‑line formatted records to
    ``logs/run_<timestamp>.log`` and also echoes messages to ``stdout``.
    Subsequent calls return the same logger instance without adding extra
    handlers.
    """
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Prevent double‑logging via the root logger.

    # Attach a JSON file handler.
    logger.addHandler(_create_file_handler())

    # Also attach a simple stream handler for console feedback.
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(stream_handler)

    _LOGGER = logger
    return logger

def log_dict(message: Dict[str, Any], level: int = logging.INFO) -> None:
    """
    Convenience helper to log a dictionary as a JSON record.

    Parameters
    ----------
    message:
        Dictionary that will be merged into the log entry. Keys must be JSON‑serialisable.
    level:
        Logging level (default ``logging.INFO``).
    """
    logger = get_logger()
    # ``extra`` merges the dict into the LogRecord; we keep the human‑readable
    # message minimal.
    logger.log(level, json.dumps(message, ensure_ascii=False), extra=message)
