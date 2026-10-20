"""
Timeout enforcement utilities for the orchestrator pipeline.

This module provides:
* `PipelineTimeoutError` – exception raised when a timeout is exceeded.
* `enforce_pipeline_timeout` – decorator that enforces a hard timeout
  on the wrapped function.
* `run_with_timeout` – helper to execute a callable with a timeout.
* `calculate_remaining_budget` – compute remaining seconds given elapsed
  time and a budget.
* `check_budget_remaining` – boolean check if time budget is still
  available.
"""

import time
import functools
from typing import Callable, Any, Tuple

class PipelineTimeoutError(RuntimeError):
    """Raised when a pipeline step exceeds its allotted wall‑clock budget."""
    pass

def calculate_remaining_budget(elapsed_seconds: float, budget_seconds: float) -> float:
    """Return the remaining budget (seconds). Never negative."""
    remaining = budget_seconds - elapsed_seconds
    return remaining if remaining > 0 else 0.0

def check_budget_remaining(elapsed_seconds: float, budget_seconds: float) -> bool:
    """Return True if the elapsed time is within the budget."""
    return elapsed_seconds <= budget_seconds

def run_with_timeout(func: Callable[..., Any], timeout_seconds: float, *args, **kwargs) -> Any:
    """
    Execute ``func`` and raise :class:`PipelineTimeoutError` if it runs longer
    than ``timeout_seconds``. The function is executed synchronously; this
    helper is intentionally simple and avoids OS‑specific signal handling
    to remain portable in the CI environment.
    """
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    if elapsed > timeout_seconds:
        raise PipelineTimeoutError(
            f"Function {func.__name__!r} exceeded timeout of {timeout_seconds}s "
            f"(elapsed {elapsed:.2f}s)."
        )
    return result

def enforce_pipeline_timeout(budget_seconds: float) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator that enforces a hard wall‑clock budget on the wrapped callable.
    If the wrapped function returns after the budget has been exceeded,
    a :class:`PipelineTimeoutError` is raised. The decorator does **not**
    attempt to pre‑empt the function; it only checks the elapsed time
    after the call returns.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            if elapsed > budget_seconds:
                raise PipelineTimeoutError(
                    f"Execution of {func.__name__!r} exceeded hard timeout of "
                    f"{budget_seconds}s (elapsed {elapsed:.2f}s)."
                )
            return result
        return wrapper
    return decorator
