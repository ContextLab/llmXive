"""
Error Handling Framework for llmXive pipeline.

This module provides custom exceptions, retry logic with exponential backoff,
timeout handling, and fatal error management for dataset downloads,
inference operations, and API failures.
"""

import time
import logging
import signal
import sys
import os
import hashlib
import threading
from typing import Callable, Optional, Any, TypeVar, Type
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Custom Exceptions ---

class InferenceTimeoutError(Exception):
    """Raised when LLM inference exceeds the allowed time limit."""
    pass

class DatasetDownloadError(Exception):
    """Raised when dataset download fails after all retries."""
    pass

class RetryExhaustedError(Exception):
    """Raised when a retryable operation fails after maximum attempts."""
    pass

class DataRetrievalError(Exception):
    """Raised when critical data retrieval (e.g., PubMed) fails fatally."""
    pass

class ValidationGateFailedError(Exception):
    """Raised when a validation gate (e.g., human pilot) fails."""
    pass

class DependencyError(Exception):
    """Raised when a required dependency is missing or invalid."""
    pass

class DataAmbiguityError(Exception):
    """Raised when data sources are ambiguous or conflicting."""
    pass


# --- Retry Logic with Exponential Backoff ---

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
) -> Callable[..., T]:
    """
    Decorator to retry a function with exponential backoff.

    Args:
        func: The function to retry.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds.
        max_delay: Maximum delay in seconds.
        exponential_base: Base for exponential growth.
        jitter: If True, adds random jitter to delay.
        exceptions: Tuple of exception types to catch and retry.

    Returns:
        The wrapped function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        attempt = 0
        while attempt < max_retries:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                attempt += 1
                if attempt == max_retries:
                    logger.error(f"Retry exhausted for {func.__name__} after {max_retries} attempts.")
                    raise RetryExhaustedError(
                        f"Function {func.__name__} failed after {max_retries} retries: {str(e)}"
                    ) from e

                # Calculate delay with exponential backoff
                delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                if jitter:
                    import random
                    delay = delay * (0.5 + random.random() * 0.5)

                logger.warning(
                    f"Attempt {attempt}/{max_retries} failed for {func.__name__}. "
                    f"Retrying in {delay:.2f}s... Error: {str(e)}"
                )
                time.sleep(delay)
        # Should not reach here, but handle gracefully
        raise RetryExhaustedError(f"Unexpected exit from retry loop for {func.__name__}")

    return wrapper


# --- Timeout Handling ---

class UnixTimeoutContext:
    """Context manager for enforcing timeouts on Unix-like systems."""
    def __init__(self, seconds: int, error_message: str = "Operation timed out"):
        self.seconds = seconds
        self.error_message = error_message
        self.old_handler = None

    def __enter__(self):
        def handler(signum, frame):
            raise TimeoutError(self.error_message)
        self.old_handler = signal.signal(signal.SIGALRM, handler)
        signal.alarm(self.seconds)

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
        if self.old_handler is not None:
            signal.signal(signal.SIGALRM, self.old_handler)
        return False


class WindowsTimeoutContext:
    """Context manager for enforcing timeouts on Windows (thread-based)."""
    def __init__(self, seconds: int, error_message: str = "Operation timed out"):
        self.seconds = seconds
        self.error_message = error_message
        self.timer = None
        self.timed_out = False

    def _timeout_handler(self):
        self.timed_out = True
        # Note: Cannot raise exception directly in main thread from timer
        # Caller must check self.timed_out

    def __enter__(self):
        self.timed_out = False
        self.timer = threading.Timer(self.seconds, self._timeout_handler)
        self.timer.daemon = True
        self.timer.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer:
            self.timer.cancel()
        if self.timed_out:
            raise TimeoutError(self.error_message)
        return False


def timeout_context(seconds: int, error_message: str = "Operation timed out"):
    """
    Factory to select the appropriate timeout context based on OS.

    Args:
        seconds: Timeout duration in seconds.
        error_message: Error message to raise on timeout.

    Returns:
        A context manager instance.
    """
    if os.name == 'nt':
        return WindowsTimeoutContext(seconds, error_message)
    else:
        return UnixTimeoutContext(seconds, error_message)


def enforce_inference_timeout(func: Callable, timeout_seconds: int = 60):
    """
    Decorator to enforce a timeout on inference functions.

    Args:
        func: The inference function to wrap.
        timeout_seconds: Maximum allowed execution time.

    Returns:
        The wrapped function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            with timeout_context(timeout_seconds, f"Inference timed out after {timeout_seconds}s"):
                return func(*args, **kwargs)
        except TimeoutError as e:
            logger.error(str(e))
            raise InferenceTimeoutError(str(e)) from e
    return wrapper


def run_inference_with_timeout(func: Callable, timeout_seconds: int = 60):
    """
    Helper to run an inference function with timeout enforcement.

    Args:
        func: The function to run.
        timeout_seconds: Timeout limit.

    Returns:
        The result of the function.

    Raises:
        InferenceTimeoutError: If the function exceeds the timeout.
    """
    return enforce_inference_timeout(func, timeout_seconds)


# --- Signal Handler Factory ---

def signal_handler_factory(signum: int, frame) -> None:
    """
    Factory for signal handlers to raise exceptions on timeout.

    Args:
        signum: Signal number.
        frame: Current stack frame.

    Raises:
        TimeoutError: Always raised.
    """
    raise TimeoutError(f"Received signal {signum}, aborting operation.")


def configure_signal_handler(timeout_seconds: int = 60):
    """
    Configure a signal handler for timeout enforcement (Unix only).

    Args:
        timeout_seconds: Duration after which the signal is triggered.
    """
    if os.name != 'nt':
        signal.signal(signal.SIGALRM, signal_handler_factory)
        signal.alarm(timeout_seconds)
        logger.info(f"Configured SIGALRM for {timeout_seconds}s timeout.")
    else:
        logger.warning("Signal-based timeout not supported on Windows.")


# --- Utility Functions ---

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal digest string.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise


def safe_download_with_retry(
    url: str,
    dest_path: str,
    max_retries: int = 3,
    base_delay: float = 2.0
) -> bool:
    """
    Download a file with retry logic and backoff.

    Args:
        url: Source URL.
        dest_path: Destination file path.
        max_retries: Maximum retry attempts.
        base_delay: Base delay for backoff.

    Returns:
        True if download successful.

    Raises:
        DatasetDownloadError: If download fails after retries.
    """
    import urllib.request
    import urllib.error

    @retry_with_backoff(
        max_retries=max_retries,
        base_delay=base_delay,
        exceptions=(urllib.error.URLError, urllib.error.HTTPError, ConnectionError)
    )
    def _download():
        logger.info(f"Downloading {url} to {dest_path}...")
        os.makedirs(os.path.dirname(dest_path) or '.', exist_ok=True)
        urllib.request.urlretrieve(url, dest_path)
        logger.info(f"Downloaded successfully: {dest_path}")
        return True

    try:
        _download()
        return True
    except RetryExhaustedError as e:
        logger.error(f"Download failed permanently: {e}")
        raise DatasetDownloadError(f"Failed to download {url} after {max_retries} retries") from e
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        raise DatasetDownloadError(f"Download failed: {e}") from e