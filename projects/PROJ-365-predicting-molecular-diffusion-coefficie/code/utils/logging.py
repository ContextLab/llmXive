"""
Centralised logging utilities for the project.

The logger writes to ``data/logs/ingestion.log`` and prefixes each message
with a timestamp. Helper functions expose the required log tags:

* ``[MISSING_DATA_EXCLUDED]`` – logged when a CSV row is dropped because
  required fields are missing.
* ``[ERROR_SMILES]`` – logged when a SMILES string cannot be parsed by RDKit.

The public API matches the names listed in the project's API surface.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Mapping

from utils.config import get_log_path, get_project_root


def get_log_file_path() -> Path:
    """
    Return the absolute path to the ingestion log file
    ``data/logs/ingestion.log``.  The parent directory is created if it
    does not already exist.
    """
    # ``get_log_path`` is defined in ``utils.config`` and points to the
    # ``data/logs`` directory.  If it is not defined, fall back to a sensible
    # default under the project root.
    try:
        base_dir = get_log_path()
    except Exception:
        base_dir = get_project_root() / "data" / "logs"

    log_file = base_dir / "ingestion.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    return log_file


def _configure_logger() -> logging.Logger:
    """
    Configure (or retrieve) a logger named ``ingestion`` that writes to the
    ingestion log file with a simple ``[timestamp] level: message`` format.
    """
    logger = logging.getLogger("ingestion")
    if logger.handlers:
        # Logger already configured – avoid adding duplicate handlers.
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(get_log_file_path(), mode="a", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Also output to stdout for interactive runs (optional but helpful).
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def get_logger() -> logging.Logger:
    """
    Public accessor for the shared ingestion logger.
    """
    return _configure_logger()


# ----------------------------------------------------------------------
# Helper logging functions required by the specification
# ----------------------------------------------------------------------


def log_missing_data_excluded(logger: logging.Logger, row: Mapping[str, Any]) -> None:
    """
    Log that a CSV row was excluded because of missing critical data.

    The message includes the required tag ``[MISSING_DATA_EXCLUDED]`` and a
    JSON representation of the offending row for traceability.
    """
    logger.info(f"[MISSING_DATA_EXCLUDED] Row excluded: {json.dumps(dict(row))}")


def log_invalid_smiles(logger: logging.Logger, smiles: str) -> None:
    """
    Log that a SMILES string could not be parsed.

    The message includes the required tag ``[ERROR_SMILES]``.
    """
    logger.info(f"[ERROR_SMILES] Invalid SMILES string: '{smiles}'")


# ----------------------------------------------------------------------
# Convenience wrappers used throughout the code base
# ----------------------------------------------------------------------


def log_info(logger: logging.Logger, message: str) -> None:
    """Log an informational message."""
    logger.info(message)


def log_error(logger: logging.Logger, message: str) -> None:
    """Log an error message."""
    logger.error(message)


# Ensure the logger is instantiated at import time so that any module that
# imports ``utils.logging`` gets a ready‑to‑use logger.
_ = get_logger()