"""
Logging utility that writes JSON‑line (JSONL) records with an ISO‑8601 UTC
timestamp.  Each call to :meth:`JsonLineLogger.log` appends a single line
to the underlying file, making the log easy to stream‑process with tools
such as ``jq`` or ``grep``.

The implementation is deliberately lightweight and has no external
dependencies beyond the Python standard library.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Mapping

__all__ = ["JsonLineLogger", "get_logger"]


class JsonLineLogger:
    """
    Append‑only logger that writes each record as a JSON object on its own
    line.  A ``timestamp`` field (ISO‑8601, UTC) is automatically added
    unless the caller supplies one.

    Parameters
    ----------
    log_file: str | Path
        Destination file.  Parent directories are created automatically.
    """

    def __init__(self, log_file: str | Path):
        self.log_path = Path(log_file)
        # Ensure the directory hierarchy exists.
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # A lock makes the logger safe to use from multiple threads.
        self._lock = Lock()

        # Open the file in append mode with UTF‑8 encoding.
        # Keeping the handle open avoids the overhead of re‑opening on every write.
        self._file = self.log_path.open("a", encoding="utf-8")

    def log(self, record: Mapping[str, Any]) -> None:
        """
        Write ``record`` as a JSON line.

        The method shallow‑copies ``record`` so that the caller's dictionary
        is not mutated.  If the ``timestamp`` key is missing, a UTC
        ISO‑8601 timestamp is inserted.
        """
        # Create a shallow copy to avoid mutating the caller's dict.
        entry = dict(record)

        # Insert timestamp if not provided.
        entry.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

        # Serialize to JSON. ``ensure_ascii=False`` preserves any Unicode
        # characters that might appear in messages.
        line = json.dumps(entry, ensure_ascii=False)

        # Write atomically under the lock.
        with self._lock:
            self._file.write(line + "\n")
            self._file.flush()

    def close(self) -> None:
        """Close the underlying file handle."""
        with self._lock:
            if not self._file.closed:
                self._file.close()

    # Context‑manager support makes usage concise:
    #   with JsonLineLogger("logs/run.jsonl") as logger:
    #       logger.log({"event": "start"})
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def get_logger(log_path: str | Path) -> JsonLineLogger:
    """
    Convenience factory that returns a ready‑to‑use :class:`JsonLineLogger`.

    This function exists mainly for the contract tests which import
    ``get_logger`` directly from ``src.utils.logging``.
    """
    return JsonLineLogger(log_path)