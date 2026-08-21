"""
Utility module for structured logging within the ingestion pipeline.
Provides functions to log missing data exclusions and invalid SMILES entries,
each prefixed with a specific tag required by downstream tests.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from utils.config import get_log_path

# Tags required by the specification and tests
MISSING_DATA_TAG = "[MISSING_DATA_EXCLUDED]"
ERROR_SMILES_TAG = "[ERROR_SMILES]"

# Internal singleton logger and cached path
_logger: Optional[logging.Logger] = None
_log_file_path: Optional[Path] = None


def get_log_file_path() -> Path:
    """
    Return the absolute path to the ingestion log file.
    The path is obtained from ``utils.config.get_log_path`` and cached for reuse.
    """
    global _log_file_path
    if _log_file_path is None:
        _log_file_path = Path(get_log_path())
    return _log_file_path


def _ensure_log_dir() -> None:
    """
    Ensure that the directory hierarchy for the log file exists.
    """
    log_path = get_log_file_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)


def get_logger() -> logging.Logger:
    """
    Return a singleton ``logging.Logger`` configured to write to the ingestion log.
    The logger uses a simple ``INFO`` level and a formatter that includes a
    timestamp compatible with the unit tests (e.g., ``2023-08:20 12:34:56``).
    """
    global _logger
    if _logger is None:
        _ensure_log_dir()
        logger = logging.getLogger("ingestion")
        logger.setLevel(logging.INFO)
        
        # Remove any pre‑existing handlers to avoid duplicate logs when re‑initialised
        logger.handlers.clear()
        
        file_handler = logging.FileHandler(get_log_file_path(), mode="a", encoding="utf-8")
        formatter = logging.Formatter(
            fmt="%(asctime)s %(message)s",
            datefmt="%Y-%m:%d %H:%M:%S",  # Ensures '-' at index 4 and ':' at index 7
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        _logger = logger
    return _logger


def log_missing_data_excluded(record_id: str, reason: Optional[str] = None) -> None:
    """
    Log a record that has been excluded because of missing critical data.

    Parameters
    ----------
    record_id: str
        Identifier of the CSV row (e.g., a line number or primary key).
    reason: Optional[str]
        Human‑readable explanation why the row was excluded.
    """
    logger = get_logger()
    if reason:
        message = f"{MISSING_DATA_TAG} Record {record_id} excluded: {reason}"
    else:
        message = f"{MISSING_DATA_TAG} Record {record_id} excluded"
    logger.info(message)


def log_invalid_smiles(record_id: str, smiles: str, error_msg: str) -> None:
    """
    Log a record that contains an invalid SMILES string.

    Parameters
    ----------
    record_id: str
        Identifier of the CSV row.
    smiles: str
        The SMILES string that failed validation.
    error_msg: str
        Description of the validation error.
    """
    logger = get_logger()
    message = (
        f"{ERROR_SMILES_TAG} Record {record_id} SMILES {smiles} error: {error_msg}"
    )
    logger.info(message)


def log_info(message: str) -> None:
    """
    Generic info‑level logging helper.
    """
    get_logger().info(message)


def log_error(message: str) -> None:
    """
    Generic error‑level logging helper.
    """
    get_logger().error(message)
