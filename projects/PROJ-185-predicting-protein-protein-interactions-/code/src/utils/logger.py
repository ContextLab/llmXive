"""
Logger utilities for the pipeline.

This module provides:
- JSONFormatter: a logging.Formatter that outputs log records as JSON lines
  with the required fields ``timestamp``, ``level``, ``message`` and
  ``schema_version``.
- get_logger: returns a configured ``logging.Logger`` instance that writes
  to ``pipeline.log`` in the current working directory.
- log_cli_invocation: helper to log the CLI command line invocation.
- log_error: helper to log an error message with ``ERROR`` level.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

__all__ = [
    "JSONFormatter",
    "get_logger",
    "log_cli_invocation",
    "log_error",
]


class JSONFormatter(logging.Formatter):
    """
    Formatter that serialises a log record to a JSON line.

    The JSON object contains the following mandatory fields:

    - ``timestamp``: ISO‑8601 UTC timestamp of the log event.
    - ``level``: Logging level name (e.g. ``INFO``, ``ERROR``).
    - ``message``: The log message (after ``%``‑style formatting).
    - ``schema_version``: Version of the log schema (currently ``1``).
    """

    def __init__(self, *, schema_version: int = 1):
        super().__init__()
        self.schema_version = schema_version

    def format(self, record: logging.LogRecord) -> str:
        # Build the JSON payload.
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "schema_version": self.schema_version,
        }
        # Ensure deterministic key order for easier testing / diffing.
        return json.dumps(payload, sort_keys=True)


_LOGGER_NAME = "pipeline_logger"
_LOG_FILE_NAME = "pipeline.log"
_LOGGER: Optional[logging.Logger] = None


def _create_logger() -> logging.Logger:
    """
    Initialise the singleton logger.

    The logger writes JSON‑Line records to ``pipeline.log`` in the current
    working directory.  It is configured with a single ``FileHandler`` using
    :class:`JSONFormatter`.  Propagation to the root logger is disabled to
    avoid duplicate output.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Ensure we do not add duplicate handlers if this function is called
    # multiple times (e.g. during test reloads).
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        log_path = Path.cwd() / _LOG_FILE_NAME
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger


def get_logger() -> logging.Logger:
    """
    Return the pipeline logger instance.

    The logger is created on first call and cached for subsequent calls.
    """
    global _LOGGER
    if _LOGGER is None:
        _LOGGER = _create_logger()
    return _LOGGER


def log_cli_invocation(argv: Optional[list] = None) -> None:
    """
    Log the command‑line invocation of the pipeline.

    Parameters
    ----------
    argv : list, optional
        ``sys.argv``‑style argument list.  If omitted, ``sys.argv`` is used.
    """
    if argv is None:
        argv = sys.argv
    command_str = " ".join(argv)
    get_logger().info(f"CLI invocation: {command_str}")


def log_error(message: str, exc_info: bool = True) -> None:
    """
    Log an error message at ``ERROR`` level.

    Parameters
    ----------
    message : str
        Human‑readable error description.
    exc_info : bool, default True
        Include exception traceback information if an exception is being
        handled.
    """
    get_logger().error(message, exc_info=exc_info)
