"""
Logger utilities for the LLM impact evaluation pipeline.

This module provides:
  - JSON‑line structured logging for pipeline events.
  - Simple counters for processed / skipped PRs (used by the timeout
    wrapper and other stages).
  - A thin wrapper around :pyfunc:`config.settings.ensure_directories`
    that accepts an optional list of extra paths (the original
    implementation mistakenly defined ``ensure_directories`` with no
    parameters, causing a TypeError in ``src.cli.main``).

The implementation is deliberately lightweight and has no external
runtime dependencies beyond the Python standard library and the
project's own ``config.settings`` module.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

# Project configuration helpers
from config.settings import get_paths, ensure_directories as _ensure_directories

# ----------------------------------------------------------------------
# Internal state
# ----------------------------------------------------------------------
_pr_processed_counter: int = 0
_pr_skipped_counter: int = 0

# ----------------------------------------------------------------------
# Helper – ensure directories (public API expected by src.cli.main)
# ----------------------------------------------------------------------
def ensure_directories(extra_paths: Optional[List[Path]] = None) -> None:
    """
    Public wrapper matching the signature used by ``src.cli.main``.

    Delegates to ``config.settings.ensure_directories`` which creates the
    core project directories and any additional paths supplied by the
    caller.

    Args:
        extra_paths: Optional list of ``Path`` objects (files or
                    directories) that should be created in addition to
                    the standard layout.
    """
    # ``config.settings.ensure_directories`` already accepts an optional
    # list, so we simply forward the argument.
    _ensure_directories(extra_paths)

# ----------------------------------------------------------------------
# Logger configuration
# ----------------------------------------------------------------------
def _json_formatter(record: logging.LogRecord) -> str:
    """
    Convert a LogRecord into a JSON‑encoded string.

    The JSON object contains a minimal set of fields required for the
    structured logs used in the research pipeline:

    - timestamp (ISO‑8601)
    - level (e.g. INFO, DEBUG)
    - logger (name of the logger)
    - message (the formatted log message)
    - module / function (optional, for debugging)

    This function is used as a ``logging.Formatter`` ``format`` method.
    """
    log_entry = {
        "timestamp": record.created,
        "level": record.levelname,
        "logger": record.name,
        "message": record.getMessage(),
        "module": record.module,
        "function": record.funcName,
    }
    return json.dumps(log_entry, ensure_ascii=False)

class JsonLineFormatter(logging.Formatter):
    """Formatter that outputs one JSON object per log line."""
    def format(self, record: logging.LogRecord) -> str:
        return _json_formatter(record)

def setup_pipeline_logging() -> None:
    """
    Configure the root logger for the entire pipeline.

    - Ensures the ``logs`` directory exists.
    - Adds a ``FileHandler`` that writes JSON‑line entries to
      ``logs/pipeline.log``.
    - Adds a ``StreamHandler`` for console output (plain text).
    - Sets the default log level to ``INFO`` (DEBUG can be enabled via
      ``--verbose`` in the CLI).
    """
    paths = get_paths()
    log_dir = Path(paths["logs"])
    # Use the public ``ensure_directories`` wrapper; it accepts a list.
    ensure_directories([log_dir])

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Prevent adding duplicate handlers if this function is called
    # multiple times (e.g., during unit tests).
    if any(isinstance(h, logging.FileHandler) and h.baseFilename.endswith("pipeline.log") for h in logger.handlers):
        return

    # File handler – JSON lines
    file_handler = logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8")
    file_handler.setFormatter(JsonLineFormatter())
    logger.addHandler(file_handler)

    # Console handler – human‑readable
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

# ----------------------------------------------------------------------
# Counter helpers (used by timeout wrapper and other stages)
# ----------------------------------------------------------------------
def increment_pr_processed() -> None:
    """Increment the counter for successfully processed PRs."""
    global _pr_processed_counter
    _pr_processed_counter += 1

def increment_pr_skipped() -> None:
    """Increment the counter for PRs that were skipped (e.g., timeout)."""
    global _pr_skipped_counter
    _pr_skipped_counter += 1

def get_pr_counters() -> dict:
    """
    Return the current PR counters.

    Returns:
        dict: ``{'processed': int, 'skipped': int}``
    """
    return {
        "processed": _pr_processed_counter,
        "skipped": _pr_skipped_counter,
    }

# ----------------------------------------------------------------------
# Convenience getter for module‑level loggers
# ----------------------------------------------------------------------
def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a named logger that inherits the pipeline configuration.

    Args:
        name: Name of the logger (typically ``__name__``).

    Returns:
        Configured ``logging.Logger`` instance.
    """
    return logging.getLogger(name)