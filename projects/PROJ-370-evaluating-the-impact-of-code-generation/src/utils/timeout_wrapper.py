"""
Global timeout wrapper for the pipeline.

The wrapper tracks the wall‑clock start time of the pipeline and a
user‑specified timeout (in seconds).  It provides a small API used
by ``src.cli.main`` and the utility logger:

* ``set_global_timeout(seconds)`` – initialise the timeout.
* ``check_timeout()`` – return ``True`` if the timeout has been
  exceeded.
* ``get_remaining_time_seconds()`` – how many seconds are left.
* ``log_timeout_warning()`` – write a warning to ``logs/timeout.log``.
* ``get_timeout_context()`` – return an object with an ``exceeded``
  attribute (``True`` when the timeout was hit).  This mirrors the
  original specification that expected a context object.
"""

import time
import threading
from pathlib import Path
from typing import Optional

_timeout_seconds: Optional[float] = None
_start_time: Optional[float] = None
_lock = threading.Lock()

class _TimeoutContext:
    """Simple container exposing whether the timeout was exceeded."""
    def __init__(self) -> None:
        self.exceeded: bool = False

_timeout_ctx = _TimeoutContext()

def set_global_timeout(seconds: float) -> None:
    """
    Initialise the global timeout.

    Parameters
    ----------
    seconds: float
        Timeout duration in seconds.
    """
    global _timeout_seconds, _start_time, _timeout_ctx
    with _lock:
        _timeout_seconds = seconds
        _start_time = time.time()
        _timeout_ctx = _TimeoutContext()

def _elapsed() -> float:
    """Return elapsed seconds since ``set_global_timeout`` was called."""
    if _start_time is None:
        return 0.0
    return time.time() - _start_time

def check_timeout() -> bool:
    """
    Return ``True`` if the configured timeout has been exceeded.

    If no timeout has been set, this function returns ``False``.
    """
    if _timeout_seconds is None:
        return False
    exceeded = _elapsed() > _timeout_seconds
    if exceeded:
        _timeout_ctx.exceeded = True
    return exceeded

def get_remaining_time_seconds() -> float:
    """
    Return the remaining time budget in seconds (zero if already timed out).
    """
    if _timeout_seconds is None or _start_time is None:
        return float("inf")
    remaining = _timeout_seconds - _elapsed()
    return max(0.0, remaining)

def log_timeout_warning() -> None:
    """
    Write a warning line to ``logs/timeout.log`` indicating that the
    global timeout has been reached.
    """
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "timeout.log"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"[TIMEOUT] Global timeout of {_timeout_seconds} seconds exceeded at {time.time():.2f}\\n")

def get_timeout_context() -> _TimeoutContext:
    """
    Return the internal timeout context object.  Callers can inspect
    the ``exceeded`` attribute to decide on exit handling.
    """
    return _timeout_ctx
