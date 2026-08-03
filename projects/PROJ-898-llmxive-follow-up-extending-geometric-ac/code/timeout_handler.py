"""
Timeout handling utilities for the llmXive project.
Provides context managers and functions for managing operation timeouts.
"""
import logging
import signal
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional, Any, Tuple
import sys

from .utils import setup_logging


@dataclass
class TimeoutResult:
    """Result of a timed operation."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    elapsed_ms: float = 0.0
    timed_out: bool = False


class TimeoutError(Exception):
    """Exception raised when an operation times out."""
    pass


class TimeoutHandler:
    """
    Handler for managing operation timeouts.
    Supports both threading-based and signal-based timeouts.
    """

    def __init__(self, timeout_seconds: float, use_signal: bool = False):
        """
        Initialize the timeout handler.

        Args:
            timeout_seconds: Maximum allowed time for the operation.
            use_signal: If True, use signal-based timeout (Unix only).
                        If False, use threading-based timeout.
        """
        self.timeout_seconds = timeout_seconds
        self.use_signal = use_signal
        self.logger = setup_logging()

    def _timeout_handler(self, signum, frame):
        """Signal handler for timeout."""
        raise TimeoutError(f"Operation timed out after {self.timeout_seconds} seconds")

    def run(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> TimeoutResult:
        """
        Run a function with a timeout.

        Args:
            func: Function to run.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            TimeoutResult with the outcome.
        """
        start_time = time.time()
        result = TimeoutResult(success=False, elapsed_ms=0.0)

        try:
            if self.use_signal and sys.platform != 'win32':
                # Signal-based timeout (Unix only)
                old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
                signal.alarm(int(self.timeout_seconds))
                try:
                    func_result = func(*args, **kwargs)
                    elapsed = time.time() - start_time
                    result = TimeoutResult(
                        success=True,
                        result=func_result,
                        elapsed_ms=elapsed * 1000
                    )
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                # Threading-based timeout
                thread_result = [None]
                thread_error = [None]

                def target():
                    try:
                        thread_result[0] = func(*args, **kwargs)
                    except Exception as e:
                        thread_error[0] = str(e)

                thread = threading.Thread(target=target)
                thread.daemon = True
                thread.start()
                thread.join(timeout=self.timeout_seconds)

                elapsed = time.time() - start_time

                if thread.is_alive():
                    result = TimeoutResult(
                        success=False,
                        error=f"Operation timed out after {self.timeout_seconds} seconds",
                        elapsed_ms=elapsed * 1000,
                        timed_out=True
                    )
                elif thread_error[0]:
                    result = TimeoutResult(
                        success=False,
                        error=thread_error[0],
                        elapsed_ms=elapsed * 1000
                    )
                else:
                    result = TimeoutResult(
                        success=True,
                        result=thread_result[0],
                        elapsed_ms=elapsed * 1000
                    )

        except TimeoutError as e:
            elapsed = time.time() - start_time
            result = TimeoutResult(
                success=False,
                error=str(e),
                elapsed_ms=elapsed * 1000,
                timed_out=True
            )
        except Exception as e:
            elapsed = time.time() - start_time
            result = TimeoutResult(
                success=False,
                error=str(e),
                elapsed_ms=elapsed * 1000
            )

        return result

    def __call__(self, func: Callable, timeout_seconds: Optional[float] = None):
        """
        Decorator to add timeout to a function.

        Args:
            func: Function to decorate.
            timeout_seconds: Override timeout (uses instance default if None).

        Returns:
            Decorated function.
        """
        def wrapper(*args, **kwargs):
            effective_timeout = timeout_seconds or self.timeout_seconds
            handler = TimeoutHandler(effective_timeout, self.use_signal)
            return handler.run(func, *args, **kwargs)
        return wrapper


def main():
    """Main entry point for testing the timeout handler."""
    logger = setup_logging()
    logger.info("Testing TimeoutHandler...")

    def slow_function(duration):
        time.sleep(duration)
        return "Completed"

    handler = TimeoutHandler(timeout_seconds=2.0)

    # Test successful completion
    result = handler.run(slow_function, 1.0)
    logger.info(f"Successful run: {result.success}, elapsed: {result.elapsed_ms:.2f}ms")

    # Test timeout
    result = handler.run(slow_function, 5.0)
    logger.info(f"Timed out run: {result.success}, timed_out: {result.timed_out}, elapsed: {result.elapsed_ms:.2f}ms")

    logger.info("TimeoutHandler tests completed.")


if __name__ == "__main__":
    main()
