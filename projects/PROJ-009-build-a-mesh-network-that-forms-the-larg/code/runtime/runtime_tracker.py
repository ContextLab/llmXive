"""
Minimal runtime‑tracking utilities used by the orchestrator CLI.

The original implementation missed an import for ``Tuple`` which caused a
``NameError`` during import.  This module now provides two simple helpers:

* ``start()`` – records the current monotonic time.
* ``stop(limit_seconds)`` – returns a tuple ``(elapsed_seconds, within_limit)``.
  ``within_limit`` is ``True`` when the elapsed time does not exceed the
  supplied limit.

The helpers are deliberately lightweight; they avoid any external
dependencies and work on any platform supported by the CI runner.
"""

import time
from typing import Tuple

from llmxive_toolkit import get_logger

log = get_logger(__name__)

_start_time: float | None = None

def start() -> None:
    """
    Record the start time of the pipeline.  Subsequent calls to ``stop``
    will compute the elapsed time relative to this timestamp.
    """
    global _start_time
    _start_time = time.monotonic()
    log.debug("Runtime tracking started at %.6f", _start_time)

def stop(limit_seconds: float) -> Tuple[float, bool]:
    """
    Compute the elapsed time since ``start()`` and report whether the
    elapsed time is within *limit_seconds*.

    Returns:
        (elapsed_seconds, within_limit)
    """
    if _start_time is None:
        raise RuntimeError("runtime_tracker.stop() called before start()")
    elapsed = time.monotonic() - _start_time
    within = elapsed <= limit_seconds
    log.debug(
        "Runtime tracking stopped: elapsed=%.3f s, limit=%.3f s, within=%s",
        elapsed,
        limit_seconds,
        within,
    )
    return elapsed, within
