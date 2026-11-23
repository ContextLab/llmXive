"""
Global timeout utilities for the research pipeline.

The module provides:
* ``set_global_timeout`` – initialise the timeout budget.
* ``check_timeout`` / ``check_global_timeout`` – enforce the limit,
  writing a JSON‑lines entry to ``logs/timeout.log`` and exiting with
  status 143 when the limit is exceeded.
* ``get_remaining_time_seconds`` – remaining budget in seconds.
* ``log_timeout_warning`` – helper that logs a warning line.
* ``get_timeout_context`` – simple context object exposing ``exceeded``.
"""

import json
import sys
import time
from pathlib import Path
from typing import NamedTuple

# ----------------------------------------------------------------------
# Constants – paths are created relative to the project root.
# ----------------------------------------------------------------------
START_TIME_FILE: Path = Path("logs/.start_time")
TIMEOUT_LOG_PATH: Path = Path("logs/timeout.log")
# Default global timeout (6 hours) – can be overridden via ``set_global_timeout``.
TIMEOUT_LIMIT_SECONDS: int = 6 * 60 * 60

# Internal state
_global_deadline: float | None = None

class _TimeoutContext(NamedTuple):
    exceeded: bool

def _ensure_log_dir() -> None:
    """Make sure the ``logs`` directory exists."""
    TIMEOUT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def set_global_timeout(seconds: float) -> None:
    """
    Initialise the global timeout budget.

    The function writes the current timestamp to ``START_TIME_FILE`` and
    stores the deadline (start + seconds) in module‑level state.
    """
    global _global_deadline, TIMEOUT_LIMIT_SECONDS

    TIMEOUT_LIMIT_SECONDS = int(seconds)
    start_ts = time.time()
    START_TIME_FILE.write_text(str(start_ts), encoding="utf-8")
    _global_deadline = start_ts + seconds

def _load_start_time() -> float:
    """Read the start timestamp from ``START_TIME_FILE``."""
    try:
        return float(START_TIME_FILE.read_text(encoding="utf-8").strip())
    except Exception as e:
        raise RuntimeError(f"Unable to read start time file {START_TIME_FILE}: {e}")

def check_timeout() -> bool:
    """
    Check whether the global timeout has been exceeded.

    Returns ``True`` if the deadline has passed, otherwise ``False``.
    If the deadline is exceeded the function writes a JSON‑lines entry
    to ``logs/timeout.log`` and **exits** the process with code 143.
    """
    if _global_deadline is None:
        # No deadline set – treat as no timeout.
        return False

    now = time.time()
    if now >= _global_deadline:
        # Log the timeout event and exit.
        log_timeout_warning()
        sys.exit(143)
    return False

# ----------------------------------------------------------------------
# Compatibility layer for the original test suite
# ----------------------------------------------------------------------
def check_global_timeout() -> None:
    """
    Compatibility wrapper used by the test suite.

    It invokes ``check_timeout`` and raises ``SystemExit`` with code 143
    when the timeout is exceeded. The wrapper mirrors the original
    behaviour expected by ``tests/unit/test_utils.py``.
    """
    if _global_deadline is None:
        # Initialise with the default limit if the caller never set it.
        set_global_timeout(TIMEOUT_LIMIT_SECONDS)

    now = time.time()
    start_ts = _load_start_time()
    if now - start_ts > TIMEOUT_LIMIT_SECONDS:
        log_timeout_warning()
        raise SystemExit(143)

def get_remaining_time_seconds() -> float:
    """
    Return the number of seconds remaining until the global deadline.
    If no deadline is set, returns ``float('inf')``.
    """
    if _global_deadline is None:
        return float("inf")
    return max(0.0, _global_deadline - time.time())

def log_timeout_warning() -> None:
    """
    Write a single JSON‑lines warning entry to ``logs/timeout.log``.
    The entry contains a timestamp and a short message.
    """
    _ensure_log_dir()
    entry = {
        "timestamp": time.time(),
        "event": "Global timeout",
        "message": "The pipeline exceeded the configured global timeout.",
    }
    with TIMEOUT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def get_timeout_context() -> _TimeoutContext:
    """
    Return a lightweight context object indicating whether the timeout
    has been exceeded. This mirrors the ``TimeoutContext`` used by the
    original CLI implementation.
    """
    exceeded = False
    if _global_deadline is not None and time.time() >= _global_deadline:
        exceeded = True
    return _TimeoutContext(exceeded=exceeded)
