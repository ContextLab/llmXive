"""
parse_failure_logger.py
------------------------

Centralised logging infrastructure for recording parse failures during
processing of source files.  Logs are written to a CSV file with the
following columns:

    * timestamp (ISO‑8601)
    * file_path  (the path of the file that failed to parse)
    * error_type (the exception class name)
    * error_msg  (the exception message)

The module provides:
    * ``init_logger`` – initialise (or re‑initialise) the logger with a
      custom CSV destination.
    * ``log_parse_failure`` – convenience wrapper that records a failure.
The logger is automatically initialised on import using the default CSV
location under the project's ``data`` directory.
"""

import csv
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

# -------------------------------------------------------------------------
# Default location for the CSV log file.
# The module lives in ``projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/``.
# Two levels up is the project root, where the ``data`` folder resides.
# -------------------------------------------------------------------------
DEFAULT_CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "parse_failures.csv"

# Global logger instance (created on first call to ``init_logger``)
_logger: Optional[logging.Logger] = None
# Global path to the CSV file used by the logger
CSV_PATH: Path = DEFAULT_CSV_PATH
# Thread‑safety lock for file writes
_write_lock = threading.Lock()


class _CSVHandler(logging.Handler):
    """
    A minimal ``logging.Handler`` that appends rows to a CSV file.
    """

    def __init__(self, csv_path: Path):
        super().__init__()
        self.csv_path = csv_path
        # Ensure the CSV file exists and has a header row.
        if not self.csv_path.exists():
            # Create parent directories if necessary
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            with self.csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["timestamp", "file_path", "error_type", "error_msg"]
                )

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
        """
        Write a single log record as a CSV row.
        """
        try:
            msg = self.format(record)
            # The ``msg`` is a pipe‑separated string: file_path|error_type|error_msg
            file_path, error_type, error_msg = msg.split("|", maxsplit=2)
            timestamp = datetime.utcnow().isoformat()
            with _write_lock, self.csv_path.open(
                "a", newline="", encoding="utf-8"
            ) as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, file_path, error_type, error_msg])
        except Exception:  # pragma: no cover
            self.handleError(record)


def init_logger(csv_path: Optional[Path] = None) -> logging.Logger:
    """
    Initialise (or re‑initialise) the ``parse_failure`` logger.

    Parameters
    ----------
    csv_path:
        Optional custom path for the CSV log file.  If omitted the default
        location ``data/parse_failures.csv`` is used.

    Returns
    -------
    logging.Logger
        The configured logger instance.
    """
    global _logger, CSV_PATH

    if csv_path is not None:
        CSV_PATH = csv_path

    logger = logging.getLogger("parse_failure")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Remove any existing handlers to avoid duplicate entries when re‑initialising.
    for h in list(logger.handlers):
        logger.removeHandler(h)

    handler = _CSVHandler(CSV_PATH)
    # Use a simple formatter that creates a pipe‑separated payload.
    formatter = logging.Formatter("%(file_path)s|%(error_type)s|%(error_msg)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    _logger = logger
    return logger


def log_parse_failure(file_path: str, error: Exception) -> None:
    """
    Record a parse failure for *file_path* with the associated *error*.

    This is a thin wrapper around the ``parse_failure`` logger that injects
    the required ``extra`` fields for the CSV formatter.

    Parameters
    ----------
    file_path:
        Path (relative or absolute) of the file that could not be parsed.
    error:
        The exception raised while parsing.
    """
    if _logger is None:
        # Lazy initialisation using the default CSV location.
        init_logger()
    # ``extra`` dict supplies the fields referenced by the formatter.
    _logger.info(
        "",  # The message itself is unused; the formatter uses ``extra``.
        extra={
            "file_path": file_path,
            "error_type": type(error).__name__,
            "error_msg": str(error),
        },
    )


# Initialise the logger automatically on module import.
init_logger()
