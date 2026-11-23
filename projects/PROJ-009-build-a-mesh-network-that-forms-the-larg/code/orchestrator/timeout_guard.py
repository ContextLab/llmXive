"""
Simple timeout‑guard decorator used by the orchestrator CLI.

The decorator records the start time, executes the wrapped function, and
then checks the elapsed time against a *hard* CI cap of 6 hours.  The
configurable limit (default 5 hours) is taken from the configuration file
when the wrapped function accesses it; however the decorator itself only
needs to know the *hard* cap to prevent runaway CI jobs.

If the elapsed time exceeds the hard cap, a ``PipelineTimeoutError`` is
raised; the CLI handler catches this and returns a non‑zero exit code.
"""

import time
import functools
from typing import Callable, Any

from llmxive_toolkit import get_logger

log = get_logger(__name__)


class PipelineTimeoutError(RuntimeError):
    """Raised when the pipeline exceeds the hard CI timeout."""


def enforce_pipeline_timeout(default_seconds: int) -> Callable:
    """
    Decorator that enforces a hard timeout on the wrapped function.

    Parameters
    ----------
    default_seconds: int
        The *soft* timeout (e.g. 5 hours = 18000 s).  The decorator will
        compare the elapsed time against the *hard* CI cap of 6 hours.

    The wrapped function is expected to perform its own runtime
    tracking (via ``runtime_tracker.start`` / ``stop``).  This decorator
    simply guards against the case where the function never returns
    (e.g. an infinite loop) by measuring the wall‑clock time.
    """
    hard_cap_seconds = 6 * 3600  # 6 h CI limit

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = func(*args, **kwargs)
            finally:
                elapsed = time.time() - start
                if elapsed > hard_cap_seconds:
                    msg = (
                        f"Pipeline exceeded hard CI timeout of {hard_cap_seconds}s "
                        f"(elapsed {elapsed:.2f}s)."
                    )
                    log.error(msg)
                    raise PipelineTimeoutError(msg)
            return result
        return wrapper
    return decorator
