import csv
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

# Thread‑safe lock for CSV writes
_lock = threading.Lock()

# Module‑level singleton logger and path
_logger: Optional[logging.Logger] = None
_log_file_path: Optional[Path] = None


def init_logger(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Initialise (or retrieve) a logger that records parse failures to a CSV file.

    Parameters
    ----------
    log_file: Optional[Path]
        Destination CSV file. If omitted, defaults to
        ``<project_root>/data/parse_failures.csv``.

    Returns
    -------
    logging.Logger
        A configured logger named ``parse_failure_logger``.
    """
    global _logger, _log_file_path

    # Return existing logger if already created
    if _logger is not None:
        return _logger

    # Resolve default location relative to the project root (two levels up from this file)
    if log_file is None:
        project_root = Path(__file__).resolve().parents[2]
        log_file = project_root / "data" / "parse_failures.csv"

    _log_file_path = log_file

    # Ensure the parent directory exists
    _log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Create logger instance
    logger = logging.getLogger("parse_failure_logger")
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers if init_logger is called multiple times
    if not logger.handlers:
        # Simple stream handler for console output; CSV handling is done manually
        stream_handler = logging.StreamHandler()
        logger.addHandler(stream_handler)

    _logger = logger

    # Initialise the CSV file with a header if it does not yet exist
    with _lock:
        if not _log_file_path.is_file():
            with _log_file_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["timestamp", "file_path", "error_message"]
                )
                writer.writeheader()

    return logger


def log_parse_failure(
    file_path: str, error_message: str, logger: Optional[logging.Logger] = None
) -> None:
    """
    Record a parse‑failure incident to the CSV log.

    Parameters
    ----------
    file_path: str
        Path of the source file that failed to parse.
    error_message: str
        Human‑readable description of the parsing error.
    logger: Optional[logging.Logger]
        Logger to emit a one‑line INFO message. If omitted, the singleton logger
        created by :func:`init_logger` is used.
    """
    # Ensure the logger (and underlying CSV path) are initialised
    if logger is None:
        logger = _logger or init_logger()

    timestamp = datetime.utcnow().isoformat()
    row = {
        "timestamp": timestamp,
        "file_path": file_path,
        "error_message": error_message,
    }

    # Append the row to the CSV in a thread‑safe manner
    with _lock:
        with _log_file_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["timestamp", "file_path", "error_message"]
            )
            writer.writerow(row)

    # Emit a concise log message for console / log aggregation
    logger.info(f"Parse failure logged for {file_path}: {error_message}")
