"""
Timeout enforcement module for the entire pipeline.
Implements FR‑007 (hard CI timeout) and provides utilities used by
the benchmark and scheduler.
"""
import signal
import time
from datetime import datetime, timezone
from typing import Callable, Any, TypeVar
from functools import wraps
import threading

from orchestrator.logger import get_logger
from orchestrator.config import get_config

logger = get_logger(__name__)

class PipelineTimeoutError(Exception):
    """Raised when the pipeline exceeds the allowed time budget."""
    pass

T = TypeVar('T')

def enforce_pipeline_timeout(timeout_seconds: int = None):
    """
    Decorator to enforce a hard timeout for the pipeline.

    If ``timeout_seconds`` is omitted the CI timeout configured in
    ``orchestrator.config.Config`` is used.
    """
    if timeout_seconds is None:
        # Fallback to the global CI timeout
        timeout_seconds = get_config().ci_timeout_seconds

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            start_time = time.time()

            def timeout_handler(signum, frame):
                elapsed = time.time() - start_time
                raise PipelineTimeoutError(
                    f"Pipeline exceeded timeout of {timeout_seconds}s after {elapsed:.2f}s"
                )

            # Set the signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorator

def run_with_timeout(func: Callable[..., T], timeout: int, *args, **kwargs) -> T:
    """
    Run a function with a timeout using a background thread.
    Raises ``PipelineTimeoutError`` if the function does not complete in time.
    """
    result_container: dict = {}
    exception_container: dict = {}

    def target():
        try:
            result_container['result'] = func(*args, **kwargs)
        except Exception as e:
            exception_container['exception'] = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        raise PipelineTimeoutError(f"Function {func.__name__} timed out after {timeout} seconds")

    if 'exception' in exception_container:
        raise exception_container['exception']

    return result_container.get('result')

def calculate_remaining_budget(start_time: datetime) -> float:
    """
    Calculate the remaining time budget (in seconds) based on the global CI timeout.
    """
    now = datetime.now(timezone.utc)
    elapsed = (now - start_time).total_seconds()
    config = get_config()
    remaining = max(0.0, config.ci_timeout_seconds - elapsed)
    logger.debug(f"Elapsed: {elapsed:.2f}s, Remaining budget: {remaining:.2f}s")
    return remaining

def check_budget_remaining(start_time: datetime, required_seconds: int) -> bool:
    """
    Check whether there is enough remaining budget for an operation that needs
    ``required_seconds`` seconds.
    Returns ``True`` if sufficient budget remains, ``False`` otherwise.
    """
    remaining = calculate_remaining_budget(start_time)
    enough = remaining >= required_seconds
    logger.debug(
        f"Budget check: need {required_seconds}s, remaining {remaining:.2f}s -> {'enough' if enough else 'insufficient'}"
    )
    return enough
