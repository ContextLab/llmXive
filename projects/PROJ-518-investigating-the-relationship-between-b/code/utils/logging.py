"""
Utility module for logging data inclusion/exclusion decisions.

This module provides a single function `log_exclusion` that records
exclusion events to a CSV-formatted log file. The log is stored under
the project's data directory in the ``interim`` sub‑folder, matching the
convention used throughout the pipeline (see quickstart.md).

The function is deliberately lightweight and has no external side‑effects
besides creating the log file (and its parent directories) if they do not
already exist.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

# Project‑wide utilities from llmxive_toolkit
from llmxive_toolkit import paths, get_logger

# Optional logger (useful for debugging pipelines)
log = get_logger(__name__)

# Standardized exclusion reason codes (as required by FR‑009)
REASON_CODES = {"MISSING_SCAN", "MISSING_SCORE", "HIGH_MOTION"}

def _validate_reason(reason: str) -> str:
    """
    Validate that the supplied reason is one of the standardized codes.
    If the reason is not recognised, a ``ValueError`` is raised.

    Parameters
    ----------
    reason : str
        The exclusion reason code supplied by the caller.

    Returns
    -------
    str
        The validated reason (identical to the input if valid).

    Raises
    ------
    ValueError
        If ``reason`` is not one of the allowed codes.
    """
    if reason not in REASON_CODES:
        raise ValueError(
            f"Invalid exclusion reason '{reason}'. "
            f"Allowed codes are: {', '.join(sorted(REASON_CODES))}."
        )
    return reason

def log_exclusion(reason: str, subject_id: str) -> None:
    """
    Append an exclusion record to the CSV log file.

    The log file is located at ``data/interim/data_exclusion_log.txt``.
    Each row contains the subject identifier, the standardized exclusion
    reason, and an ISO‑8601 timestamp.

    Parameters
    ----------
    reason : str
        Standardized exclusion reason code (e.g. ``'MISSING_SCAN'``).
    subject_id : str
        Identifier of the subject that is being excluded.

    Raises
    ------
    ValueError
        If ``reason`` is not a recognized exclusion code.
    """
    # Validate the reason code early to avoid silent logging of bad data.
    _validate_reason(reason)

    # Resolve the log file path using the llmxive_toolkit helper.
    # This guarantees the file lives inside the project root and that
    # the ``interim`` directory is created if it does not exist.
    log_path: Path = paths.data("interim", "data_exclusion_log.txt")

    # Ensure the parent directory exists.
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Timestamp in ISO‑8601 format (e.g., ``2026-10-13T15:42:07.123456``)
    timestamp: str = datetime.now().isoformat()

    # Determine whether we need to write the CSV header.
    file_exists: bool = log_path.is_file()

    # Append the new row.
    with log_path.open("a", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["subject_id", "reason", "timestamp"]
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(
            {
                "subject_id": subject_id,
                "reason": reason,
                "timestamp": timestamp,
            }
        )

    log.debug(
        "Logged exclusion: subject_id=%s, reason=%s, timestamp=%s",
        subject_id,
        reason,
        timestamp,
    )
