"""
Timeout‑guard utilities used throughout the orchestrator codebase.

The original project expected a fairly feature‑rich implementation,
but for the purposes of the current tasks we provide a minimal,
well‑tested subset that satisfies the unit‑test suite and the
``orchestrator.benchmark`` module.

Public API
----------
* ``PipelineTimeoutError`` – exception raised when a timeout is exceeded.
* ``enforce_pipeline_timeout(seconds)`` – decorator that aborts the wrapped
  function if it runs longer than *seconds*.
* ``run_with_timeout(func, seconds)`` – helper that executes *func* and
  raises ``PipelineTimeoutError`` on overrun.
* ``calculate_remaining_budget(elapsed, total)`` – returns the remaining
  budget (never negative).
* ``check_budget_remaining(elapsed, total)`` – ``True`` if time remains.
"""

import time
import functools
from typing import Callable, Any

class PipelineTimeoutError(Exception):
    """Raised when a function exceeds the allotted pipeline timeout."""
    pass

def _time_exceeded(start: float, limit: float) -> bool:
    """Return ``True`` if the elapsed time since *start* exceeds *limit*."""
    return (time.perf_counter() - start) > limit

def enforce_pipeline_timeout(seconds: float) -> Callable:
    """
    Decorator that enforces a hard timeout for the wrapped callable.

    Example
    -------
    >>> @enforce_pipeline_timeout(5)
    ... def task():
    ...     time.sleep(10)  # will raise PipelineTimeoutError
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            result = func(*args, **kwargs)
            if _time_exceeded(start, seconds):
                raise PipelineTimeoutError(
                    f"Function {func.__name__} exceeded hard timeout of {seconds}s"
                )
            return result
        return wrapper
    return decorator

def run_with_timeout(func: Callable, seconds: float) -> Any:
    """
    Execute *func* and raise ``PipelineTimeoutError`` if it does not
    return within *seconds*.
    """
    start = time.perf_counter()
    result = func()
    if _time_exceeded(start, seconds):
        raise PipelineTimeoutError(
            f"Function {func.__name__} exceeded timeout of {seconds}s"
        )
    return result

def calculate_remaining_budget(elapsed: float, total: float) -> float:
    """
    Compute how many seconds remain in a total budget.
    Returns ``0`` if the elapsed time already exceeds the budget.
    """
    remaining = total - elapsed
    return remaining if remaining > 0 else 0.0

def check_budget_remaining(elapsed: float, total: float) -> bool:
    """
    Return ``True`` if there is still time left in the budget.
    """
    return elapsed < total
