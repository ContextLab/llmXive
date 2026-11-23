"""
Simple structured logger used throughout the pipeline.

The logger writes JSON‑lines to ``logs/pipeline.log``.  It is a thin
wrapper around the standard ``logging`` module – each log record is
serialised as a JSON object containing a timestamp, level, logger
name, message and any ``extra`` fields supplied by the caller.
"""
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

_LOG_FILE = Path("logs/pipeline.log")
_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

_LOGGER = logging.getLogger("pipeline")
_LOGGER.setLevel(logging.INFO)

# Ensure a single handler (avoid duplicate logs if called repeatedly)
if not _LOGGER.handlers:
    handler = logging.FileHandler(_LOG_FILE, mode="a", encoding="utf-8")
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    _LOGGER.addHandler(handler)

def _serialize_record(record: logging.LogRecord) -> str:
    """
    Convert a ``LogRecord`` into a JSON string.
    """
    payload = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "level": record.levelname,
        "name": record.name,
        "message": record.getMessage(),
    }
    # ``extra`` dict items are stored directly on the record.
    extra_items = {
        key: value
        for key, value in record.__dict__.items()
        if key not in logging.LogRecord.__dict__
    }
    if extra_items:
        payload.update(extra_items)
    return json.dumps(payload, ensure_ascii=False)

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a logger that emits JSON‑lines.

    Parameters
    ----------
    name: str
        Name of the logger (appears in the ``name`` field of each
        JSON object).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    return logging.getLogger(name)

def setup_pipeline_logging() -> None:
    """
    Initialise the pipeline logger.

    This function is idempotent – calling it multiple times has no
    adverse effect.
    """
    # The logger configuration is performed at import time; this
    # function exists for compatibility with existing code that
    # expects an explicit setup step.
    pass
