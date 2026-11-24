"""
Global timeout handling utilities.

The original test suite (``tests/unit/test_utils.py``) expects the
following public names:

* ``START_TIME_FILE`` – ``Path`` to the file that stores the epoch
  start time of the pipeline.
* ``TIMEOUT_LOG_PATH`` – ``Path`` to the JSON‑lines log that records
  timeout events.
* ``TIMEOUT_LIMIT_SECONDS`` – numeric limit (default 3600 s).
* ``check_global_timeout`` – function that aborts with exit code 143
  when the elapsed time exceeds the limit.
* ``set_global_timeout`` – helper that creates the start‑time file.
* ``check_timeout`` – alias kept for backward compatibility.

The implementation is deliberately tiny and has no external
dependencies beyond the standard library.
"""
import json
import sys
import time
from pathlib import Path
from typing import Optional

# ----------------------------------------------------------------------
# Configuration constants (can be overridden by callers via monkeypatch)
# ----------------------------------------------------------------------
TIMEOUT_LIMIT_SECONDS: int = 3600  # 1 hour default
START_TIME_FILE: Path = Path("logs/.start_time")
TIMEOUT_LOG_PATH: Path = Path("logs/timeout.log")

# Ensure the log directory exists at import time.
TIMEOUT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def set_global_timeout(limit_seconds: Optional[int] = None,
                      start_file: Optional[Path] = None) -> None:
    """
    Initialise the global timeout mechanism.

    Parameters
    ----------
    limit_seconds: int | None
        If provided, overrides ``TIMEOUT_LIMIT_SECONDS``.
    start_file: Path | None
        Path to the file that will store the start timestamp.  If
        omitted the default ``START_TIME_FILE`` is used.
    """
    global TIMEOUT_LIMIT_SECONDS, START_TIME_FILE
    if limit_seconds is not None:
        TIMEOUT_LIMIT_SECONDS = int(limit_seconds)
    if start_file is not None:
        START_TIME_FILE = Path(start_file)

    # Write the current epoch time to the start‑time file.
    START_TIME_FILE.parent.mkdir(parents=True, exist_ok=True)
    with START_TIME_FILE.open("w", encoding="utf-8") as fp:
        fp.write(str(time.time()))

def _write_timeout_event() -> None:
    """
    Append a JSON‑lines timeout event to ``TIMEOUT_LOG_PATH``.
    """
    event = {
        "event": "Global timeout",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "limit_seconds": TIMEOUT_LIMIT_SECONDS,
    }
    with TIMEOUT_LOG_PATH.open("a", encoding="utf-8") as fp:
        json.dump(event, fp, ensure_ascii=False)
        fp.write("\n")

def check_global_timeout() -> None:
    """
    Abort the process if the elapsed time exceeds ``TIMEOUT_LIMIT_SECONDS``.

    The function reads the timestamp from ``START_TIME_FILE``.  If the
    file does not exist, it is created with the current time (meaning
    the check will never fire on the first call).

    On timeout the function writes a JSON‑lines entry to
    ``TIMEOUT_LOG_PATH`` and raises ``SystemExit(143)``.
    """
    # Ensure a start time exists.
    if not START_TIME_FILE.is_file():
        # Initialise lazily.
        set_global_timeout()

    try:
        with START_TIME_FILE.open("r", encoding="utf-8") as fp:
            start_ts = float(fp.read().strip())
    except Exception:
        # Corrupted file – treat as never started.
        start_ts = time.time()
        with START_TIME_FILE.open("w", encoding="utf-8") as fp:
            fp.write(str(start_ts))

    elapsed = time.time() - start_ts
    if elapsed > TIMEOUT_LIMIT_SECONDS:
        _write_timeout_event()
        sys.exit(143)

# Backward‑compatibility alias used elsewhere in the code base.
def check_timeout() -> None:
    """Alias for :func:`check_global_timeout`."""
    check_global_timeout()
