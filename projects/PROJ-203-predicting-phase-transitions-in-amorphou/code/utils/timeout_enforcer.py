"""
Timeout Enforcer Utility for Pipeline Execution.

Provides a context manager to enforce a maximum wall‑clock time for
pipeline execution stages, ensuring compliance with the 6‑hour budget.
Also supplies auxiliary helpers expected by the rest of the codebase.
"""
import time
import logging
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

class PipelineTimeoutError(TimeoutError):
    """Exception raised when the pipeline execution exceeds the allowed time."""
    pass


class TimeoutEnforcer:
    """
    Context manager to enforce a maximum execution time.

    Initializes a timer on entry. If the time limit is exceeded upon exit,
    raises :class:`PipelineTimeoutError`. This class is used throughout the
    pipeline (e.g., in ``code/main.py``) and provides the ``elapsed_seconds``
    attribute for reporting.
    """

    def __init__(self, max_seconds: float = 21600.0, log_path: Optional[str] = None):
        """
        Initialize the timeout enforcer.

        Args:
            max_seconds: Maximum time allowed (default 6 hours = 21600 s).
            log_path: Optional path to log timeout events.
        """
        self.max_seconds = max_seconds
        self.log_path = log_path
        self._start_time: Optional[float] = None
        self.elapsed_seconds: float = 0.0

    def __enter__(self):
        """Start the timer upon entering the context."""
        self._start_time = time.time()
        logger.info(f"PipelineTimeout context entered. Max duration: {self.max_seconds}s")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Check elapsed time upon exiting the context.

        If the elapsed time exceeds the limit, log the event and raise
        :class:`PipelineTimeoutError`.
        """
        if self._start_time is None:
            # Should never happen, but guard against misuse.
            return False

        self.elapsed_seconds = time.time() - self._start_time

        if self.elapsed_seconds > self.max_seconds:
            msg = (
                f"Pipeline execution exceeded timeout limit. "
                f"Elapsed: {self.elapsed_seconds:.2f}s, Limit: {self.max_seconds:.2f}s"
            )
            logger.error(msg)

            if self.log_path:
                try:
                    with open(self.log_path, "a") as f:
                        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} TIMEOUT: {msg}\n")
                except IOError as e:
                    logger.warning(f"Failed to write timeout log to {self.log_path}: {e}")

            raise PipelineTimeoutError(msg)

        logger.info(f"Pipeline execution completed within limit. Elapsed: {self.elapsed_seconds:.2f}s")
        # Returning False propagates any exception that occurred inside the block.
        return False


@contextmanager
def pipeline_timeout(max_seconds: float = 21600.0, log_path: Optional[str] = None):
    """
    Functional wrapper for :class:`TimeoutEnforcer`.

    Allows ``with pipeline_timeout(...):`` syntax without explicitly
    instantiating the class.
    """
    with TimeoutEnforcer(max_seconds, log_path):
        yield


# ----------------------------------------------------------------------
# Helper utilities expected by other modules
# ----------------------------------------------------------------------

def get_remaining_time(enforcer: Optional[TimeoutEnforcer] = None) -> Optional[float]:
    """
    Return the remaining time (in seconds) before the timeout is reached.

    If an ``enforcer`` instance is provided, the remaining time is computed
    from its start time and ``max_seconds``. If no enforcer is given (or the
    enforcer has not been started), ``None`` is returned.

    This function is imported in ``code/main.py`` but not currently used;
    providing it avoids import errors and keeps the public API stable.
    """
    if enforcer is None or enforcer._start_time is None:
        return None
    elapsed = time.time() - enforcer._start_time
    remaining = enforcer.max_seconds - elapsed
    return max(remaining, 0.0)