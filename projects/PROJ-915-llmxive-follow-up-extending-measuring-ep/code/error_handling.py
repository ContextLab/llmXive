"""
Error Handling Framework.
Provides retry logic, timeout handling, and custom exceptions.
"""
import time
import logging
import signal
import sys
import os
import hashlib
import threading
from pathlib import Path
from typing import Callable, Optional, Any, TypeVar, Type

T = TypeVar('T')

# Custom Exceptions
class InferenceTimeoutError(Exception):
    """Raised when inference exceeds the time limit."""
    pass

class DatasetDownloadError(Exception):
    """Raised when dataset download fails after retries."""
    pass

class RetryExhaustedError(Exception):
    """Raised when retry attempts are exhausted."""
    pass

class DataRetrievalError(Exception):
    """Raised when data retrieval (e.g., PubMed) fails critically."""
    pass

class ValidationGateFailedError(Exception):
    """Raised when a validation gate (e.g., human pilot) fails."""
    pass

class DependencyError(Exception):
    """Raised when a required dependency is missing."""
    pass

class DataAmbiguityError(Exception):
    """Raised when data is ambiguous or insufficient for analysis."""
    pass

# Retry Logic
def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable[..., T]:
    """
    Decorator to retry a function with exponential backoff.
    """
    def wrapper(*args, **kwargs) -> T:
        last_exception = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (backoff_factor ** attempt)
                    logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logging.error(f"All {max_retries} attempts failed.")
                    raise RetryExhaustedError(f"Function {func.__name__} failed after {max_retries} attempts.") from e
        raise last_exception # Should not reach here
    return wrapper

# Timeout Logic
def timeout_context(timeout_seconds: float):
    """
    Context manager to enforce a timeout on a block of code.
    Note: This works reliably on Unix. On Windows, it uses a thread-based fallback.
    """
    if os.name == 'nt':
        return WindowsTimeoutContext(timeout_seconds)
    else:
        return UnixTimeoutContext(timeout_seconds)

class UnixTimeoutContext:
    def __init__(self, timeout_seconds: float):
        self.timeout = timeout_seconds

    def __enter__(self):
        # Save the old handler
        self.old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(int(self.timeout))

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
        signal.signal(signal.SIGALRM, self.old_handler)
        if exc_type is signal.SIGALRM:
            raise InferenceTimeoutError(f"Operation timed out after {self.timeout} seconds.")

    @staticmethod
    def _timeout_handler(signum, frame):
        raise InferenceTimeoutError("Timeout signal received.")

class WindowsTimeoutContext:
    """Fallback for Windows using threading."""
    def __init__(self, timeout_seconds: float):
        self.timeout = timeout_seconds
        self.timer = None
        self.timed_out = False

    def _on_timeout(self):
        self.timed_out = True

    def __enter__(self):
        self.timer = threading.Timer(self.timeout, self._on_timeout)
        self.timer.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer:
            self.timer.cancel()
        if self.timed_out:
            raise InferenceTimeoutError(f"Operation timed out after {self.timeout} seconds.")

def enforce_inference_timeout(func: Callable, timeout_seconds: float):
    """
    Decorator to enforce a timeout on an inference function.
    """
    def wrapper(*args, **kwargs):
        with timeout_context(timeout_seconds):
            return func(*args, **kwargs)
    return wrapper

def run_inference_with_timeout(func: Callable, timeout_seconds: float, *args, **kwargs):
    """
    Run an inference function with a timeout.
    """
    with timeout_context(timeout_seconds):
        return func(*args, **kwargs)

def signal_handler_factory(sig_num):
    """Factory for signal handlers."""
    def handler(signum, frame):
        raise InferenceTimeoutError(f"Timeout signal {sig_num} received.")
    return handler

def configure_signal_handler():
    """Configure signal handlers for timeout."""
    if os.name != 'nt':
        signal.signal(signal.SIGALRM, signal_handler_factory(signal.SIGALRM))

# Hashing utilities
def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def safe_download_with_retry(url: str, dest_path: str, max_retries: int = 3) -> bool:
    """
    Safe download with retry logic.
    Simplified implementation for demonstration.
    """
    @retry_with_backoff(max_retries=max_retries, exceptions=(DatasetDownloadError,))
    def _download():
        try:
            # Placeholder for actual download logic
            # In real code, use requests or urllib
            import urllib.request
            urllib.request.urlretrieve(url, dest_path)
            return True
        except Exception as e:
            raise DatasetDownloadError(f"Download failed: {e}")

    return _download()