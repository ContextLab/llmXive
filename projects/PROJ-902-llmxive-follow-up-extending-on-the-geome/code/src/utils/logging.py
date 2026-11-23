"""
Logging utility for the llmXive project.

Provides a JSON‑line logger that records each log entry as a JSON object
on a separate line. Each entry includes a UTC ISO‑8601 timestamp,
the log level, the message, and optional extra fields.

Public API (as declared in the project API surface):
  - JsonLineLogger
  - setup_logger
  - get_logger
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Mapping, Optional

# Global registry to reuse logger instances per log file path
_LOGGER_REGISTRY: dict[Path, "JsonLineLogger"] = {}
_REGISTRY_LOCK = Lock()


class JsonLineLogger:
    """
    Simple thread‑safe JSON‑line logger.

    Parameters
    ----------
    log_path : Path
        Destination file for log entries. The file is opened in append mode.
    """

    def __init__(self, log_path: Path):
        self.log_path = log_path
        # Ensure parent directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        # Open file handle in append mode, text, UTF‑8
        self._file = open(self.log_path, "a", encoding="utf-8")
        self._lock = Lock()

    def _write(self, entry: Mapping[str, Any]) -> None:
        """Serialise a mapping as a JSON line and write it atomically."""
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock:
            self._file.write(line + "\n")
            self._file.flush()

    def _make_entry(self, level: str, message: str, **extra: Any) -> dict[str, Any]:
        """
        Build the log entry dictionary.

        The timestamp is produced in UTC and formatted as an ISO‑8601 string
        with microsecond precision (e.g., ``2023-08-13T12:34:56.123456+00:00``).
        """
        timestamp = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        entry: dict[str, Any] = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
        }
        if extra:
            entry.update(extra)
        return entry

    # Public logging methods -------------------------------------------------
    def info(self, message: str, **extra: Any) -> None:
        self._write(self._make_entry("INFO", message, **extra))

    def warning(self, message: str, **extra: Any) -> None:
        self._write(self._make_entry("WARNING", message, **extra))

    def error(self, message: str, **extra: Any) -> None:
        self._write(self._make_entry("ERROR", message, **extra))

    def debug(self, message: str, **extra: Any) -> None:
        self._write(self._make_entry("DEBUG", message, **extra))

    def close(self) -> None:
        """Close the underlying file handle."""
        with self._lock:
            if not self._file.closed:
                self._file.close()

    # Ensure the file is closed when the logger is garbage‑collected
    def __del__(self):
        self.close()


def setup_logger(log_file: str | os.PathLike) -> JsonLineLogger:
    """
    Initialise (or retrieve) a ``JsonLineLogger`` for the given path.

    This function is the canonical way for library code to obtain a logger.
    It guarantees that multiple calls with the same ``log_file`` return the
    same logger instance, avoiding duplicate file handles.

    Parameters
    ----------
    log_file : str | PathLike
        Destination file for log entries.

    Returns
    -------
    JsonLineLogger
        Configured logger instance.
    """
    path = Path(log_file).expanduser().resolve()
    with _REGISTRY_LOCK:
        if path not in _LOGGER_REGISTRY:
            _LOGGER_REGISTRY[path] = JsonLineLogger(path)
        return _LOGGER_REGISTRY[path]


def get_logger(log_file: str | os.PathLike = "app.log") -> JsonLineLogger:
    """
    Convenience wrapper used by the test suite and downstream code.

    It simply forwards to :func:`setup_logger`. The default log file
    ``app.log`` resides in the current working directory if no explicit
    path is supplied.

    Parameters
    ----------
    log_file : str | PathLike, optional
        Destination file for log entries, by default "app.log".

    Returns
    -------
    JsonLineLogger
        The logger instance.
    """
    return setup_logger(log_file)