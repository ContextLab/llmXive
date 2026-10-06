"""
Timeout Enforcer Utility for Pipeline Execution.

Provides a context manager to enforce a maximum wall-clock time for
pipeline execution stages, ensuring compliance with the 6-hour budget.
"""
import time
import logging
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)


class PipelineTimeout(Exception):
    """Exception raised when the pipeline execution exceeds the allowed time."""
    pass


class TimeoutEnforcer:
    """
    Context manager to enforce a maximum execution time.

    Initializes a timer on entry. If the time limit is exceeded upon exit,
    raises a TimeoutError. This is designed to be used around long-running
    simulation or training blocks.

    Args:
        max_seconds (float): Maximum allowed execution time in seconds.
        log_path (Optional[str]): Path to a log file to record timeout events.
    """

    def __init__(self, max_seconds: float = 21600.0, log_path: Optional[str] = None):
        """
        Initialize the timeout enforcer.

        Args:
            max_seconds: Maximum time allowed (default 6 hours = 21600s).
            log_path: Optional path to log timeout events.
        """
        self.max_seconds = max_seconds
        self.log_path = log_path
        self.start_time: Optional[float] = None
        self.elapsed_time: float = 0.0

    def __enter__(self):
        """Start the timer upon entering the context."""
        self.start_time = time.time()
        logger.info(f"PipelineTimeout context entered. Max duration: {self.max_seconds}s")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Check elapsed time upon exiting the context.

        If the elapsed time exceeds the limit, log the event and raise TimeoutError.
        """
        if self.start_time is None:
            return False

        self.elapsed_time = time.time() - self.start_time

        if self.elapsed_time > self.max_seconds:
            msg = (f"Pipeline execution exceeded timeout limit. "
                   f"Elapsed: {self.elapsed_time:.2f}s, Limit: {self.max_seconds:.2f}s")
            logger.error(msg)

            if self.log_path:
                try:
                    with open(self.log_path, 'a') as f:
                        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} TIMEOUT: {msg}\n")
                except IOError as e:
                    logger.warning(f"Failed to write timeout log to {self.log_path}: {e}")

            raise TimeoutError(msg)

        logger.info(f"Pipeline execution completed within limit. Elapsed: {self.elapsed_time:.2f}s")
        return False


@contextmanager
def pipeline_timeout(max_seconds: float = 21600.0, log_path: Optional[str] = None):
    """
    Functional wrapper for TimeoutEnforcer context manager.

    Args:
        max_seconds: Maximum allowed duration in seconds.
        log_path: Optional path to log timeout events.

    Yields:
        None
    """
    with TimeoutEnforcer(max_seconds, log_path):
        yield
