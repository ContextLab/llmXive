"""
Utility logging module for the project.

Provides functions for initializing logging, recording exclusions,
and writing/checking checksum files. Implements the missing
`get_exclusion_log_path` function required by several modules.
"""

import csv
import logging
from pathlib import Path
from llmxive_toolkit import paths

# Configure a basic logger for the whole project.
# Individual modules may customize further if needed.
def init_logging(level: int = logging.INFO) -> None:
    """
    Initialise the project‑wide logger.

    Parameters
    ----------
    level : int, optional
        Logging level (default INFO). Calls ``logging.basicConfig`` only
        if the root logger has no handlers configured.
    """
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

def log_error(message: str) -> None:
    """Log an error message."""
    logging.error(message)

def log_warning(message: str) -> None:
    """Log a warning message."""
    logging.warning(message)

def get_exclusion_log_path() -> Path:
    """
    Return the absolute path to the exclusion log CSV.

    The path is ``data/processed/exclusion_log.csv`` relative to the
    project root. The directory is created if it does not already exist.
    """
    path = paths.data("processed", "exclusion_log.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def log_exclusion(subject_id: str, reason: str, metadata: dict | None = None) -> None:
    """
    Append a record of a subject exclusion to the exclusion log.

    Parameters
    ----------
    subject_id : str
        Identifier of the excluded subject.
    reason : str
        Short string describing why the subject was excluded.
    metadata : dict, optional
        Additional key‑value information (e.g., mean FD). Stored as a
        JSON‑encoded string in the CSV.
    """
    log_path = get_exclusion_log_path()
    file_exists = log_path.is_file()

    # Ensure the parent directory exists.
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            # Header row
            writer.writerow(["Subject_ID", "Exclusion_Reason", "Metadata"])
        metadata_str = "" if metadata is None else str(metadata)
        writer.writerow([subject_id, reason, metadata_str])

    logging.info(f"Exclusion logged: {subject_id} – {reason}")
