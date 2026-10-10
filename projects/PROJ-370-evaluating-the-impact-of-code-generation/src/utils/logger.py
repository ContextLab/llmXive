"""
Structured JSON logger utilities for the pipeline.

This module provides a simple `get_logger` function that returns a
``logging.Logger`` instance configured to write one JSON object per
line to ``logs/<logger_name>.log``.  The format includes the
timestamp, log level, logger name, message and any extra fields
passed via the ``extra`` argument of the logging call.

The logger is deliberately lightweight – it does not propagate to
the root logger and it creates the ``logs`` directory on first
use.  Helper functions ``increment_pr_processed`` and
``increment_pr_skipped`` are provided for the CLI orchestration;
they simply emit a ``INFO`` record with a ``counter`` field that
downstream analysis scripts can aggregate if desired.
"""

import json
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

class _JsonLogFormatter(logging.Formatter):
    """Format a log record as a single JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        # Base payload
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Merge any user‑supplied extra fields (the ``extra`` dict)
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            payload.update(record.extra)
        else:
            # ``logging`` stores extra fields directly on the record
            for key, value in record.__dict__.items():
                if key not in (
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
                ):
                    payload[key] = value

        return json.dumps(payload, ensure_ascii=False)

def _ensure_file_handler(logger: logging.Logger) -> None:
    """Attach a ``FileHandler`` that writes JSON lines if not already present."""
    if any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        return
    log_path = LOGS_DIR / f"{logger.name}.log"
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(_JsonLogFormatter())
    logger.addHandler(handler)
    logger.propagate = False  # Prevent duplicate output to root logger

def get_logger(name: str) -> logging.Logger:
    """
    Return a logger that writes JSON‑line records to ``logs/<name>.log``.

    Parameters
    ----------
    name: str
        Logical name of the logger (e.g., ``"pipeline"`` or
        ``"unit_test_logger"``).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    _ensure_file_handler(logger)
    return logger

# ----------------------------------------------------------------------
# Simple counter helpers used by the CLI timeout wrapper
# ----------------------------------------------------------------------
def increment_pr_processed() -> None:
    """
    Emit a log entry indicating that a PR has been successfully processed.
    Downstream scripts may count these entries.
    """
    logger = get_logger("pipeline")
    logger.info("PR processed", extra={"counter": "processed"})

def increment_pr_skipped() -> None:
    """
    Emit a log entry indicating that a PR was skipped (e.g., due to timeout).
    """
    logger = get_logger("pipeline")
    logger.info("PR skipped", extra={"counter": "skipped"})
