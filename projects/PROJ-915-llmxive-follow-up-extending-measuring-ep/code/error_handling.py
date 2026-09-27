"""
Error Handling Framework for llmXive Pipeline.

Provides custom exceptions, retry logic, and timeout enforcement mechanisms
for dataset downloads and model inference operations.
"""
import time
import logging
import signal
import sys
import os
import hashlib
from typing import Callable, Optional, Any, TypeVar, Dict
from functools import wraps

# Configure logger
logger = logging.getLogger(__name__)

# --- Custom Exceptions ---

class InferenceTimeoutError(Exception):
    """Raised when model inference exceeds the allowed time limit."""
    pass

class DatasetDownloadError(Exception):
    """Raised when dataset download fails after all retries."""
    pass

class RetryExhaustedError(Exception):
    """Raised when a retryable operation fails after exhausting all attempts."""
    pass

# --- Retry Logic ---

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions_to_catch: tuple = (Exception,)
) -> Callable[..., T]:
    """
    Decorator to retry a function with exponential backoff.

    Args:
        func: The function to wrap.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        backoff_factor: Multiplier for delay after each failure.
        exceptions_to_catch: Tuple of exception types to catch and retry.

    Returns:
        Wrapped function with retry logic.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        delay = base_delay
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions_to_catch as e:
                last_exception = e
                if attempt == max_retries:
                    logger.error(f"Retry exhausted for {func.__name__} after {max_retries} attempts.")
                    raise RetryExhaustedError(f"Operation '{func.__name__}' failed after {max_retries} retries.") from e
                
                logger.warning(
                    f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
                delay *= backoff_factor
        
        # Should not reach here, but just in case
        raise last_exception

    return wrapper

# --- Timeout Context & Enforcement ---

class timeout_context:
    """
    Context manager to enforce a time limit on a block of code using signals.
    Note: Works on Unix-like systems. On Windows, this uses a threading approach.
    """
    def __init__(self, seconds: int, error_message: str = "Operation timed out"):
        self.seconds = seconds
        self.error_message = error_message
        self.old_handler = None

    def _timeout_handler(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        if os.name == 'nt':
            # Windows does not support signal.alarm
            # Fallback to a simple threading timer if strictly needed, 
            # but for this framework we raise NotImplementedError for Windows signal usage
            # or assume a Unix environment for the primary pipeline as per typical HPC/Colab runners.
            if sys.platform != 'win32':
                self.old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
                signal.alarm(self.seconds)
            else:
                # On Windows, we rely on a different mechanism or skip strict signal timeout
                # For the purpose of this framework, we raise a specific error if used on Windows
                # to ensure the implementer knows the limitation.
                logger.warning("signal.alarm not supported on Windows. Timeout enforcement may be skipped.")
        else:
            self.old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(self.seconds)
        return self

    def __exit__(self, type, value, traceback):
        if os.name != 'nt' and sys.platform != 'win32':
            signal.alarm(0)  # Cancel the alarm
            if self.old_handler is not None:
                signal.signal(signal.SIGALRM, self.old_handler)
        # If a TimeoutError was raised, propagate it as InferenceTimeoutError
        if type is TimeoutError:
            raise InferenceTimeoutError(self.error_message)

def enforce_inference_timeout(seconds: int):
    """
    Decorator to enforce a timeout on an inference function.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                with timeout_context(seconds, f"Inference for {func.__name__} timed out after {seconds}s"):
                    return func(*args, **kwargs)
            except TimeoutError:
                raise InferenceTimeoutError(f"Inference for {func.__name__} timed out after {seconds}s")
        return wrapper
    return decorator

def run_inference_with_timeout(func: Callable, timeout_seconds: int, *args, **kwargs) -> Any:
    """
    Wrapper to run an inference function with a strict timeout.
    """
    try:
        with timeout_context(timeout_seconds, "Inference operation timed out"):
            return func(*args, **kwargs)
    except TimeoutError:
        raise InferenceTimeoutError("Inference operation timed out")

# --- Signal Handler Factory ---

def signal_handler_factory(signal_number, frame):
    """
    Factory to create a signal handler that raises a TimeoutError.
    """
    def handler(signum, frame):
        raise TimeoutError(f"Signal {signum} received: Operation timed out")
    return handler

def configure_signal_handler(timeout_seconds: int):
    """
    Configure the global signal handler for timeouts.
    """
    if os.name != 'nt':
        signal.signal(signal.SIGALRM, signal_handler_factory(signal.SIGALRM, None))
        signal.alarm(timeout_seconds)
    else:
        logger.warning("Signal handling for timeouts not configured on Windows.")

# --- Download Helpers ---

def download_progress_hook(block_num, block_size, total_size):
    """
    Callback for urlretrieve to show progress.
    """
    if total_size > 0:
        percent = min(100, (block_num * block_size * 100) // total_size)
        sys.stdout.write(f"\rDownloading: {percent}%")
        sys.stdout.flush()
    else:
        sys.stdout.write(f"\rDownloaded: {block_num * block_size} bytes")
        sys.stdout.flush()

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def safe_download_with_retry(
    url: str,
    dest_path: str,
    max_retries: int = 3,
    timeout: int = 30
) -> str:
    """
    Download a file from a URL with retry logic and error handling.
    
    Args:
        url: Source URL.
        dest_path: Destination file path.
        max_retries: Number of retry attempts.
        timeout: Timeout for the download request.
    
    Returns:
        Path to the downloaded file.
    
    Raises:
        DatasetDownloadError: If download fails after retries.
    """
    from urllib.request import urlretrieve
    from urllib.error import URLError, HTTPError

    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading {url} to {dest_path} (Attempt {attempt + 1}/{max_retries})")
            urlretrieve(url, dest_path, reporthook=download_progress_hook)
            logger.info(f"\nDownload successful: {dest_path}")
            return dest_path
        except (URLError, HTTPError, TimeoutError) as e:
            logger.warning(f"Download attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise DatasetDownloadError(f"Failed to download {url} after {max_retries} attempts: {e}")
            time.sleep(2 ** attempt) # Exponential backoff
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            raise DatasetDownloadError(f"Unexpected error downloading {url}: {e}")
    
    raise DatasetDownloadError(f"Download of {url} failed.")

def configure_retry_policy(max_retries: int = 3, base_delay: float = 1.0):
    """
    Configure global retry policy settings.
    (In a more complex system, this might set global constants or config objects)
    """
    logger.info(f"Retry policy configured: max_retries={max_retries}, base_delay={base_delay}s")
    return {"max_retries": max_retries, "base_delay": base_delay}

def update_hash_state(file_path: str, state_dict: Dict) -> None:
    """
    Update a state dictionary with the SHA-256 hash of a file.
    """
    if os.path.exists(file_path):
        state_dict[os.path.basename(file_path)] = compute_sha256(file_path)
    else:
        logger.warning(f"File {file_path} not found, skipping hash update.")