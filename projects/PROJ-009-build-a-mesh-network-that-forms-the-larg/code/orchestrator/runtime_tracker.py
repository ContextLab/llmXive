"""
Simple runtime‑tracking utilities.

The orchestrator CLI uses these helpers to record the total wall‑clock
time of a pipeline run and to enforce the hard timeout required by
FR‑007 / SC‑004.  The implementation is deliberately lightweight:
it stores the start time in a module‑level variable and, when stopped,
writes a JSON file ``data/runtime/pipeline_runtime.json`` containing:

    {
        "total_seconds": <float>,
        "within_limit": <bool>
    }

If the elapsed time exceeds the supplied hard limit (in seconds) a
``RuntimeError`` is raised; the CLI catches this and exits with a
non‑zero status.

This module also provides the ``@enforce_pipeline_timeout`` decorator
used by integration tests to verify watchdog behaviour.  When the
timeout is exceeded the decorator writes a plain‑text log file
``data/runtime/timeout_enforced.log`` containing the error message.
"""

import json
import time
from pathlib import Path
from functools import wraps

from llmxive_toolkit import paths, get_logger

_log = get_logger(__name__)

_start_ts: float | None = None


def start() -> None:
    """Record the start timestamp of the pipeline."""
    global _start_ts
    _start_ts = time.time()
    _log.debug("Runtime tracking started at %.3f", _start_ts)


def stop(hard_limit_seconds: int) -> None:
    """
    Stop the timer, write the runtime JSON, and enforce the hard limit.

    Args:
        hard_limit_seconds: Maximum allowed wall‑clock time.
    Raises:
        RuntimeError: If the elapsed time exceeds ``hard_limit_seconds``.
    """
    if _start_ts is None:
        raise RuntimeError("runtime_tracker.start() was not called")

    elapsed = time.time() - _start_ts
    within_limit = elapsed <= hard_limit_seconds

    runtime_path = paths.data("runtime", "pipeline_runtime.json")
    runtime_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "total_seconds": round(elapsed, 3),
        "within_limit": within_limit,
    }
    runtime_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _log.info(
        "Pipeline runtime recorded: %.3f s (within limit: %s)",
        elapsed,
        within_limit,
    )

    if not within_limit:
        raise RuntimeError(
            f"Pipeline exceeded hard timeout of {hard_limit_seconds}s "
            f"by {elapsed - hard_limit_seconds:.2f}s"
        )


def enforce_pipeline_timeout(max_seconds: int):
    """
    Decorator that enforces a hard pipeline timeout.

    The wrapped function is executed with runtime tracking started
    before the call and stopped afterwards.  If the elapsed time
    exceeds *max_seconds* a ``RuntimeError`` is raised (as per
    ``stop``) and an additional log file ``timeout_enforced.log``
    is written containing the error message.

    Example
    -------
    >>> @enforce_pipeline_timeout(300)
    ... def my_task():
    ...     ...

    Parameters
    ----------
    max_seconds: int
        The hard timeout in seconds.

    Returns
    -------
    Callable
        The wrapped function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Start timing
            start()
            try:
                result = func(*args, **kwargs)
            except Exception:
                # If the wrapped function itself raises, still stop timer
                try:
                    stop(max_seconds)
                except RuntimeError:
                    # Already handled below
                    pass
                raise
            # Stop timing and enforce limit
            try:
                stop(max_seconds)
            except RuntimeError as e:
                # Write the timeout log as required by the spec
                log_path = paths.data("runtime", "timeout_enforced.log")
                log_path.parent.mkdir(parents=True, exist_ok=True)
                log_path.write_text(str(e), encoding="utf-8")
                _log.error("Pipeline timeout enforced: %s", e)
                # Re‑raise so callers see a non‑zero exit
                raise
            return result
        return wrapper
    return decorator
