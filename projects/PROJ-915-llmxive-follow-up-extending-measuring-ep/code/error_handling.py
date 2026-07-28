import time
import logging
import signal
import sys
import os
import hashlib
import functools
import threading
from typing import Callable, Optional, Type, Any, List
from contextlib import contextmanager

# Configure logger
logger = logging.getLogger(__name__)

# --- Custom Exceptions ---

class InferenceTimeoutError(Exception):
    """Raised when model inference exceeds the configured time limit."""
    pass

class DatasetDownloadError(Exception):
    """Raised when dataset download fails after all retries."""
    pass

class RetryExhaustedError(Exception):
    """Raised when a retryable operation fails after exhausting all attempts."""
    pass

# --- Retry Logic ---

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 2.0,
    backoff_factor: float = 2.0,
    exceptions_to_catch: tuple = (Exception,)
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        func: The function to wrap.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        backoff_factor: Multiplier for delay after each failure.
        exceptions_to_catch: Tuple of exceptions that trigger a retry.
    
    Returns:
        The wrapped function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        delay = base_delay
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions_to_catch as e:
                last_exception = e
                if attempt == max_retries:
                    logger.error(f"Retry exhausted for {func.__name__} after {max_retries} attempts.")
                    raise RetryExhaustedError(f"Operation {func.__name__} failed after {max_retries} retries.") from e
                
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
                delay *= backoff_factor
        
        # Should not reach here, but safe fallback
        raise last_exception

    return wrapper

# --- Timeout Context & Logic ---

@contextmanager
def timeout_context(timeout_seconds: float, operation_name: str = "Operation"):
    """
    Context manager that raises InferenceTimeoutError if the block exceeds timeout.
    Uses threading.Timer for non-blocking timeout enforcement.
    
    Args:
        timeout_seconds: Time limit in seconds.
        operation_name: Name of the operation for logging.
    
    Yields:
        None
    
    Raises:
        InferenceTimeoutError: If the timeout is exceeded.
    """
    if timeout_seconds <= 0:
        yield
        return

    timer = threading.Timer(timeout_seconds, lambda: (_ for _ in ()).throw(InferenceTimeoutError(f"{operation_name} timed out after {timeout_seconds}s")))
    timer.daemon = True
    timer.start()
    try:
        yield
    finally:
        timer.cancel()

def enforce_inference_timeout(func: Callable, timeout_seconds: float) -> Callable:
    """
    Decorator to enforce a hard timeout on an inference function.
    
    Args:
        func: The inference function.
        timeout_seconds: Maximum allowed execution time.
    
    Returns:
        Wrapped function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with timeout_context(timeout_seconds, f"Inference: {func.__name__}"):
            return func(*args, **kwargs)
    return wrapper

def run_inference_with_timeout(
    func: Callable,
    timeout_seconds: float,
    *args,
    **kwargs
) -> Any:
    """
    Runs a function with a hard timeout using threading.
    If the function does not complete in time, raises InferenceTimeoutError.
    
    Args:
        func: The function to run.
        timeout_seconds: Max time allowed.
        *args: Positional arguments for func.
        **kwargs: Keyword arguments for func.
    
    Returns:
        The result of func.
    
    Raises:
        InferenceTimeoutError: If timeout is exceeded.
    """
    result_container = {"result": None, "error": None}
    
    def target():
        try:
            result_container["result"] = func(*args, **kwargs)
        except Exception as e:
            result_container["error"] = e

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        # Note: We cannot forcibly kill the thread in Python safely.
        # We raise the error to signal the caller, but the thread may continue in background.
        # For inference, usually the caller handles the timeout and abandons the request.
        raise InferenceTimeoutError(f"Inference operation timed out after {timeout_seconds}s.")

    if result_container["error"]:
        raise result_container["error"]

    return result_container["result"]

# --- Signal Handling ---

def signal_handler_factory(timeout_seconds: float, operation_name: str):
    """
    Factory to create a signal handler that raises InferenceTimeoutError.
    
    Args:
        timeout_seconds: Time limit.
        operation_name: Name of operation.
    
    Returns:
        A signal handler function.
    """
    def handler(signum, frame):
        raise InferenceTimeoutError(f"{operation_name} timed out after {timeout_seconds}s (Signal {signum}).")
    return handler

def configure_signal_handler(timeout_seconds: float, operation_name: str = "Operation"):
    """
    Configures SIGALRM to trigger a timeout error.
    Only available on Unix-like systems.
    
    Args:
        timeout_seconds: Time limit.
        operation_name: Name of operation.
    """
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, signal_handler_factory(timeout_seconds, operation_name))
    else:
        logger.warning("SIGALRM not available on this platform. Signal-based timeout disabled.")

# --- Download with Retry & Checksum ---

def download_progress_hook(t):
    """Returns a callback function for tqdm to update progress."""
    last_b = [0]
    def update_to(b=1, bsize=1, tsize=None):
        if tsize is not None:
            t.total = tsize
        t.update((b - last_b[0]) * bsize)
        last_b[0] = b
    return update_to

def compute_sha256(filepath: str) -> str:
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def safe_download_with_retry(
    url: str,
    dest_path: str,
    max_retries: int = 3,
    timeout: float = 30.0
) -> str:
    """
    Downloads a file from a URL with retry logic and progress tracking.
    Raises DatasetDownloadError if download fails.
    
    Args:
        url: Source URL.
        dest_path: Local destination path.
        max_retries: Max retry attempts.
        timeout: Timeout per request.
    
    Returns:
        Path to the downloaded file.
    
    Raises:
        DatasetDownloadError: If download fails.
    """
    try:
        import requests
        from tqdm import tqdm
    except ImportError:
        raise ImportError("Download functionality requires 'requests' and 'tqdm' packages.")

    @retry_with_backoff(
        max_retries=max_retries,
        exceptions_to_catch=(requests.exceptions.RequestException, ConnectionError, TimeoutError)
    )
    def _download():
        logger.info(f"Downloading {url} to {dest_path}...")
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        with open(dest_path, 'wb') as f, tqdm(
            desc=os.path.basename(dest_path),
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        logger.info(f"Download complete: {dest_path}")
        return compute_sha256(dest_path)

    try:
        hash_val = _download()
        logger.info(f"Checksum computed: {hash_val}")
        return dest_path
    except RetryExhaustedError as e:
        raise DatasetDownloadError(f"Failed to download {url} after {max_retries} retries.") from e
    except Exception as e:
        raise DatasetDownloadError(f"Unexpected error during download: {e}") from e

# --- Configuration & Policy ---

def configure_retry_policy(
    max_retries: int = 3,
    base_delay: float = 2.0,
    backoff_factor: float = 2.0
) -> tuple:
    """
    Returns retry parameters for use in other modules.
    
    Returns:
        Tuple of (max_retries, base_delay, backoff_factor)
    """
    return max_retries, base_delay, backoff_factor

def update_hash_state(hash_state: dict, key: str, value: str):
    """
    Updates a dictionary with a new hash state entry.
    
    Args:
        hash_state: The dictionary to update.
        key: The artifact key.
        value: The hash value.
    """
    hash_state[key] = value

# --- Main Entry Point (for testing) ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Error Handling Framework loaded successfully.")
    logger.info("Available: retry_with_backoff, timeout_context, safe_download_with_retry, InferenceTimeoutError, DatasetDownloadError")