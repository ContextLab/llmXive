import csv
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

# Module‑level state
_logger: Optional[logging.Logger] = None
_log_path: Optional[Path] = None
_lock = threading.Lock()


def init_logger(log_file: Path) -> logging.Logger:
    """
    Initialise a singleton logger used for parse‑failure reporting.

    Parameters
    ----------
    log_file: Path
        Destination CSV file where each parse failure will be recorded.
        The file is created if it does not exist and the parent directory
        is created automatically.

    Returns
    -------
    logging.Logger
        Configured logger instance (writes to stdout for visibility).
    """
    global _logger, _log_path
    _log_path = Path(log_file)
    _log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("parse_failure_logger")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if init_logger is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    _logger = logger
    return logger


def _ensure_header() -> None:
    """
    Ensure that the CSV file has a header row.  This is called lazily
    before the first write.  If the file already exists and contains data,
    the header is left untouched.
    """
    if _log_path is None:
        raise RuntimeError("Logger not initialised – call init_logger() first.")
    if not _log_path.exists():
        with _log_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "file_path", "error_type", "error_message"])


def log_parse_failure(file_path: str, error: Exception) -> None:
    """
    Record a single parse‑failure event to the CSV log.

    Parameters
    ----------
    file_path: str
        The path (relative or absolute) of the file that could not be parsed.
    error: Exception
        The exception raised during parsing (e.g., ``SyntaxError``).
    """
    if _log_path is None:
        raise RuntimeError("Logger not initialised – call init_logger() first.")

    _ensure_header()

    timestamp = datetime.utcnow().isoformat()
    row = [timestamp, file_path, type(error).__name__, str(error)]

    # Thread‑safe append
    with _lock:
        with _log_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

    # Also emit a human‑readable log line for debugging / CI visibility
    if _logger:
        _logger.info(f"Parse failure logged for {file_path}: {error}")
