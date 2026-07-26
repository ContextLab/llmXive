"""
Timeout enforcement and benchmarking logic.
Enforces fixed per-chunk duration constraints.
"""
import signal
import time
from functools import wraps
from typing import Callable, Any
from utils.logging import TimeoutError, get_logger

logger = get_logger(__name__)


class timeout_handler:
    """Context manager for enforcing timeouts using signal alarms."""
    def __init__(self, seconds: int, error_message: str = "Operation timed out"):
        self.seconds = seconds
        self.error_message = error_message
        self.timeout_error = TimeoutError(error_message, duration=seconds)

    def handle_timeout(self, signum, frame):
        raise self.timeout_error

    def __enter__(self):
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, self.handle_timeout)
            signal.alarm(self.seconds)
        else:
            # Fallback for non-Unix systems (e.g., Windows)
            self._start_time = time.time()
            self._use_alarm = False
            return self
        self._use_alarm = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._use_alarm:
            signal.alarm(0)  # Cancel alarm
        return False


def enforce_timeout(seconds: int):
    """Decorator to enforce timeout on a function."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with timeout_handler(seconds, f"Function {func.__name__} timed out"):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def main():
    """Demo timeout enforcement."""
    import time

    @enforce_timeout(2)
    def slow_function():
        logger.info("Starting slow function...")
        time.sleep(3)  # Simulate long operation
        logger.info("This should not print")
        return "Success"

    try:
        result = slow_function()
        logger.info(f"Result: {result}")
    except TimeoutError as e:
        logger.error(f"Caught expected timeout: {e}")


if __name__ == "__main__":
    main()