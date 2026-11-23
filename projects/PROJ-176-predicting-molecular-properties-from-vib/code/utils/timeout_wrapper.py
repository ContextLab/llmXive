"""
Utility that runs a callable with a hard timeout using ``signal``.
"""
import signal
from typing import Callable, Any

class TimeoutError(RuntimeError):
    pass

def _handler(signum, frame):
    raise TimeoutError("Operation timed out")

def enforce_timeout(func: Callable[..., Any], timeout_seconds: int) -> Callable[..., Any]:
    """
    Return a wrapped version of *func* that raises ``TimeoutError`` if it runs longer than
    *timeout_seconds*. The wrapper must be called (i.e. ``enforce_timeout(f, 30)()``).
    """
    def wrapper(*args, **kwargs):
        old_handler = signal.signal(signal.SIGALRM, _handler)
        signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
        try:
            return func(*args, **kwargs)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)
    return wrapper