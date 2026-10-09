"""
Structured JSON logger utilities for the research pipeline.

This module provides:
  - `get_logger(name)`: returns a configured ``logging.Logger`` instance that
    writes JSON‑line formatted records to ``logs/<name>.log``.
  - `setup_pipeline_logging()`: convenience to initialise a top‑level
    ``pipeline`` logger used by ``src.cli.main``.
  - Internal helpers for ensuring the ``logs`` directory exists and for
    formatting log records as JSON.

The logger is deliberately lightweight and avoids external dependencies.
It writes one JSON object per line, containing at least the following
fields:

  * ``timestamp`` – ISO‑8601 UTC timestamp.
  * ``task`` – the logger name (usually the module or pipeline stage).
  * ``level`` – log level name (e.g. ``INFO``).
  * ``message`` – the log message.

Additional optional fields (e.g. ``runtime_seconds``) can be injected via
the ``LogRecord`` object (``record.runtime``) if desired.
"""

import json
import datetime
import logging
from pathlib import Path
from typing import Any

# Import the project‑wide configuration utilities.
from code.config.settings import get_paths, ensure_directories

__all__ = ["get_logger", "setup_pipeline_logging"]

def _ensure_log_dirs() -> None:
    """
    Ensure that the directory defined by the ``logs`` entry in the
    configuration exists.  ``ensure_directories`` accepts a list of
    ``Path`` objects, so we forward a single‑element list containing the
    target directory.
    """
    paths = get_paths()
    log_dir = Path(paths["logs"])
    # ``ensure_directories`` creates parent directories as needed.
    ensure_directories([log_dir])

class _JSONLogFormatter(logging.Formatter):
    """
    Minimal JSON formatter for ``logging``.  It serialises a subset of the
    ``LogRecord`` attributes to a single JSON object per line.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat(),
            "task": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Allow callers to attach a ``runtime`` attribute for timing info.
        if hasattr(record, "runtime"):
            log_entry["runtime_seconds"] = getattr(record, "runtime")
        return json.dumps(log_entry, ensure_ascii=False)

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve (or create) a logger that writes JSON lines to
    ``logs/<name>.log``.  The logger is cached by the standard ``logging``
    module, so repeated calls with the same ``name`` return the same
    instance.

    Parameters
    ----------
    name: str
        Identifier for the logger – typically the module or pipeline stage.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    _ensure_log_dirs()
    logger = logging.getLogger(name)

    # Configure the logger only once – avoid duplicate handlers on repeated
    # calls (which would otherwise cause each message to be written multiple
    # times).
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        log_path = Path(get_paths()["logs"]) / f"{name}.log"
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(_JSONLogFormatter())
        logger.addHandler(handler)
    return logger

def setup_pipeline_logging() -> logging.Logger:
    """
    Initialise a top‑level ``pipeline`` logger used by the CLI entry point.
    This function is deliberately tiny – it simply ensures the log
    directory exists and returns a logger instance.  The caller can then
    emit messages such as ``logger.info("pipeline started")``.
    """
    logger = get_logger("pipeline")
    logger.info("Pipeline logging initialised")
    return logger
