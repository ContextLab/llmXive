"""
Utility for enforcing a timeout on a callable.

Provides a simple wrapper that raises ``TimeoutError`` if the wrapped
function does not return within the specified number of seconds.
"""

import signal
from typing import Callable, Any

class TimeoutError(RuntimeError):
    """Raised when a function exceeds the allotted timeout."""
    pass

def enforce_timeout(func: Callable[[], Any], timeout_seconds: int) -> Any:
    """
    Execute ``func`` and raise ``TimeoutError`` if it runs longer than
    ``timeout_seconds``.

    This implementation uses ``signal`` which works on Unix platforms
    (the CI runners are Linux based).

    Args:
        func: A callable with no arguments.
        timeout_seconds: Maximum number of seconds ``func`` may run.

    Returns:
        The return value of ``func`` if it completes in time.

    Raises:
        TimeoutError: If the execution exceeds ``timeout_seconds``.
    """
    def _handle_timeout(signum, frame):
        raise TimeoutError(f"Function timed out after {timeout_seconds} seconds")

    # Register the alarm signal handler
    original_handler = signal.signal(signal.SIGALRM, _handle_timeout)
    # Schedule the alarm
    signal.setitimer(signal.ITIMER_REAL, timeout_seconds)

    try:
        result = func()
        return result
    finally:
        # Cancel any pending alarm and restore original handler
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, original_handler)
