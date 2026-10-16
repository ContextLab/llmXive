"""
Runtime guard utility.

The ``RuntimeGuard`` class records a deadline (epoch timestamp).  When
the guard is asked to ``check`` the current time against the deadline,
it aborts the process with exit code 143 and writes a ``timeout``
event to ``logs/timeout.log``.  The guard can be used as a simple
context manager or called manually.

Example
-------
>>> from src.pipeline.runtime_guard import RuntimeGuard
>>> guard = RuntimeGuard(deadline_ts=time.time() - 10)  # already expired
>>> guard.check()   # raises SystemExit(143) and writes a log entry
"""
import json
import sys
import time
from pathlib import Path
from llmxive_toolkit import paths

# Resolve the timeout log location once.
_TIMEOUT_LOG_PATH: Path = paths.logs("timeout.log")
_TIMEOUT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

class RuntimeGuard:
    """
    Guard that enforces a global runtime deadline.

    Parameters
    ----------
    deadline_ts: float
        Epoch timestamp (as returned by ``time.time()``) after which
        the guard will trigger a timeout.
    """
    def __init__(self, deadline_ts: float):
        self.deadline_ts = float(deadline_ts)

    def _write_timeout_event(self) -> None:
        """
        Write a JSON‑lines event indicating a timeout.
        """
        event = {
            "event": "timeout",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "deadline": self.deadline_ts,
        }
        with _TIMEOUT_LOG_PATH.open("a", encoding="utf-8") as fp:
            json.dump(event, fp, ensure_ascii=False)
            fp.write("\n")

    def check(self) -> None:
        """
        Abort the process if the current time exceeds the deadline.

        If the deadline has passed, a ``SystemExit`` with exit code
        143 is raised after writing a timeout event.
        """
        if time.time() > self.deadline_ts:
            self._write_timeout_event()
            sys.exit(143)

    # Context‑manager convenience
    def __enter__(self):
        self.check()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # No special handling; just propagate any exception.
        return False
