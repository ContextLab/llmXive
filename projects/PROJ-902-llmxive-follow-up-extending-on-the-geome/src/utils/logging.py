"""
Utility for JSON‑line logging with timestamps and optional resource usage
recording.

Provides:
- JsonLineLogger: thread‑safe logger that writes a JSON object per line,
  automatically adding an ISO‑8601 UTC timestamp.
- get_logger(name, log_dir=Path("logs")): convenience factory returning a logger
  that writes to ``log_dir/<name>.jsonl``.
The logger can be used as a context manager; when exiting the ``with`` block it
records the wall‑clock time elapsed and the process peak RSS (converted to GB)
as a log entry with ``event="resource"``.
"""

import json
import time
import resource
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Mapping, Optional, Union

class JsonLineLogger:
    """
    Thread‑safe JSON‑line logger.

    Parameters
    ----------
    log_path : Union[str, Path]
        Destination file. Parent directories are created if missing.
    mode : str, optional
        File mode, default ``'a'`` (append).
    """

    def __init__(self, log_path: Union[str, Path], mode: str = "a"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.log_path, mode, encoding="utf-8")
        self._lock = Lock()
        self._start_time: Optional[float] = None
        self._start_rss: Optional[int] = None

    # --------------------------------------------------------------------- #
    # Context‑manager support – records resource usage on exit
    # --------------------------------------------------------------------- #
    def __enter__(self) -> "JsonLineLogger":
        self._start_time = time.time()
        # ru_maxrss reports the maximum resident set size used so far
        # (in KiB on Linux, bytes on macOS)
        self._start_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        end_time = time.time()
        elapsed = end_time - (self._start_time or end_time)

        # Current peak RSS (may be larger than the value captured at entry)
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Convert KiB -> GB (Linux) – on macOS ru_maxrss is in bytes.
        if peak_rss > 0 and peak_rss < 2**20:  # heuristic: likely bytes
            peak_gb = peak_rss / (1024 ** 3)
        else:
            peak_gb = peak_rss / (1024 ** 2)  # KiB -> GB

        self.log(
            {
                "event": "resource",
                "elapsed_sec": elapsed,
                "peak_ram_gb": round(peak_gb, 4),
            }
        )
        self.close()

    # --------------------------------------------------------------------- #
    # Logging API
    # --------------------------------------------------------------------- #
    def log(self, record: Mapping[str, Any]) -> None:
        """
        Write a single log entry.

        The record is copied, a ``timestamp`` field (ISO‑8601 UTC) is added,
        and the resulting JSON object is written as one line.
        """
        entry = dict(record)  # shallow copy to avoid mutating caller data
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock:
            self._file.write(line + "\n")
            self._file.flush()

    def close(self) -> None:
        """Close the underlying file handle."""
        with self._lock:
            if not self._file.closed:
                self._file.close()


def get_logger(
    name: str,
    log_dir: Union[str, Path] = Path("logs"),
    *,
    mode: str = "a"
) -> JsonLineLogger:
    """
    Convenience factory that returns a ``JsonLineLogger`` writing to
    ``log_dir/<name>.jsonl``.

    Parameters
    ----------
    name : str
        Base name of the log file (without extension).
    log_dir : Union[str, Path], optional
        Directory that will contain the log file.
    mode : str, optional
        File mode passed to ``JsonLineLogger`` (default ``'a'``).

    Returns
    -------
    JsonLineLogger
    """
    log_dir_path = Path(log_dir)
    log_path = log_dir_path / f"{name}.jsonl"
    return JsonLineLogger(log_path, mode=mode)