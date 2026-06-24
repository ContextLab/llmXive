"""
pipeline_time_limit.py
-----------------------

Utility for enforcing a global CPU time limit on the entire
prediction pipeline.  The default limit is six hours (21 600 seconds),
matching the functional requirement FR‑010 / SC‑003.

The module provides:
  * ``PipelineTimeLimitExceeded`` – custom exception raised when the
    time limit is exceeded.
  * ``time_limit`` – a context manager that installs a POSIX alarm
    (where available) and also tracks elapsed wall‑clock time as a
    fallback.
  * ``run_with_time_limit`` – a helper that runs a callable inside the
    ``time_limit`` context.
  * ``main`` – a tiny CLI useful for manual sanity‑checking.

The implementation deliberately uses only the Python standard library so
that it works on any platform supported by the project.  When the
``signal`` module cannot be used (e.g. on Windows or in non‑main threads)
the context manager falls back to a simple elapsed‑time check performed on
exit.
"""

from __future__ import annotations

import argparse
import signal
import sys
import threading
import time
from contextlib import ContextDecorator
from typing import Callable, Any, Optional

__all__ = [
    "PipelineTimeLimitExceeded",
    "time_limit",
    "run_with_time_limit",
    "main",
]


class PipelineTimeLimitExceeded(RuntimeError):
    """Raised when the pipeline exceeds the allowed CPU time limit."""

    def __init__(self, limit_seconds: int, elapsed: float) -> None:
        super().__init__(
            f"Pipeline exceeded time limit of {limit_seconds} seconds "
            f"(elapsed: {elapsed:.2f}s)."
        )
        self.limit_seconds = limit_seconds
        self.elapsed = elapsed


class time_limit(ContextDecorator):
    """
    Context manager that enforces a maximum CPU time limit.

    It attempts to use ``signal.alarm`` on Unix platforms for a
    pre‑emptive interrupt.  If ``signal`` cannot be used (e.g. on
    Windows), the manager records the start time and checks the elapsed
    time when exiting the block, raising :class:`PipelineTimeLimitExceeded`
    if the limit was breached.
    """

    def __init__(self, limit_seconds: int = 21_600) -> None:
        self.limit_seconds = limit_seconds
        self._start_time: Optional[float] = None
        self._original_handler: Optional[Callable[[int, Any], Any]] = None
        self._using_signal = False

    def _handler(self, signum: int, frame: Any) -> None:  # pragma: no cover
        """Signal handler that raises the custom exception."""
        raise PipelineTimeLimitExceeded(self.limit_seconds, self.elapsed())

    def __enter__(self) -> "time_limit":
        self._start_time = time.time()
        # Try to install a POSIX alarm; this works only in the main thread
        # on Unix‑like systems.
        if hasattr(signal, "SIGALRM"):
            try:
                self._original_handler = signal.getsignal(signal.SIGALRM)
                signal.signal(signal.SIGALRM, self._handler)
                signal.alarm(self.limit_seconds)
                self._using_signal = True
            except Exception:
                # Any failure (e.g., not in main thread) falls back to
                # elapsed‑time checking.
                self._using_signal = False
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        # Cancel any pending alarm if we set one.
        if self._using_signal:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, self._original_handler)  # type: ignore[arg-type]

        elapsed = self.elapsed()
        if exc_type is PipelineTimeLimitExceeded:
            # Propagate custom exception unchanged.
            return False
        if elapsed > self.limit_seconds:
            raise PipelineTimeLimitExceeded(self.limit_seconds, elapsed)
        # Returning False propagates any other exception (if any).
        return False

    def elapsed(self) -> float:
        """Return elapsed wall‑clock time in seconds."""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time


def run_with_time_limit(
    func: Callable[..., Any],
    *args,
    limit_seconds: int = 21_600,
    **kwargs,
) -> Any:
    """
    Execute ``func`` with the global pipeline time limit applied.

    Parameters
    ----------
    func
        Callable to be executed.
    *args, **kwargs
        Arguments forwarded to ``func``.
    limit_seconds
        Maximum allowed CPU time in seconds (default: 6 h).

    Returns
    -------
    Any
        The return value of ``func`` if it completes within the limit.

    Raises
    ------
    PipelineTimeLimitExceeded
        If the execution exceeds ``limit_seconds``.
    """
    with time_limit(limit_seconds):
        return func(*args, **kwargs)


def _demo_function(duration: int) -> str:
    """Simple function that sleeps for ``duration`` seconds."""
    time.sleep(duration)
    return f"Slept for {duration} seconds"


def main(argv: Optional[list[str]] = None) -> None:
    """
    Minimal command‑line interface for manual testing.

    Example
    -------
    $ python pipeline_time_limit.py --seconds 5 --sleep 10
    Pipeline exceeded time limit of 5 seconds (elapsed: 10.00s).
    """
    parser = argparse.ArgumentParser(
        description="Run a dummy function with a global pipeline time limit."
    )
    parser.add_argument(
        "--seconds",
        type=int,
        default=21_600,
        help="Maximum allowed CPU time in seconds (default: 21600).",
    )
    parser.add_argument(
        "--sleep",
        type=int,
        default=0,
        help="Number of seconds the demo function should sleep.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_with_time_limit(_demo_function, args.sleep, limit_seconds=args.seconds)
        print(result)
    except PipelineTimeLimitExceeded as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
