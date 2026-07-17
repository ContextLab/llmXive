import time
import logging
import signal
import sys
import os
from functools import wraps
from typing import Callable, Type, Tuple, Optional, Any, Dict
from contextlib import contextmanager
import requests
from pathlib import Path
import hashlib
import yaml

logger = logging.getLogger(__name__)

# Custom Exceptions
class InferenceTimeoutError(Exception):
    """Raised when LLM inference exceeds the allowed time limit."""
    pass

class DatasetDownloadError(Exception):
    """Raised when dataset download fails after all retries."""
    pass

class RetryExhaustedError(Exception):
    """Raised when a retryable operation fails after exhausting all attempts."""
    pass

# Retry Logic
def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (requests.RequestException, ConnectionError, TimeoutError)
):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay in seconds.
        exponential_base: Base for exponential delay calculation.
        jitter: Whether to add random jitter to the delay.
        exceptions: Tuple of exception types to catch and retry.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f"Retry exhausted for {func.__name__} after {max_retries} attempts.")
                        raise RetryExhaustedError(f"Operation {func.__name__} failed after {max_retries} retries: {str(e)}") from e
                    
                    if jitter:
                        import random
                        delay = delay * exponential_base + random.uniform(0, 0.1 * delay)
                    else:
                        delay *= exponential_base
                    
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}. Retrying in {delay:.2f}s... Error: {str(e)}")
                    time.sleep(delay)
            
            raise RetryExhaustedError(f"Operation {func.__name__} failed unexpectedly.")
        return wrapper
    return decorator

# Timeout Context Manager
@contextmanager
def timeout_context(timeout_seconds: float, operation_name: str = "Operation"):
    """
    Context manager that raises InferenceTimeoutError if the block exceeds timeout_seconds.
    Uses SIGALRM for Unix-like systems. On Windows, it uses a polling mechanism with a daemon thread.
    """
    if sys.platform != 'win32':
        # Unix implementation using SIGALRM
        def handler(signum, frame):
            raise InferenceTimeoutError(f"{operation_name} timed out after {timeout_seconds} seconds")
        
        old_handler = signal.signal(signal.SIGALRM, handler)
        old_interval = signal.getsignal(signal.SIGALRM)
        
        try:
            signal.alarm(int(timeout_seconds) + 1) # +1 to ensure we catch the exact second
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Windows implementation using threading
        import threading
        import sys
        
        timer = threading.Timer(timeout_seconds, lambda: (_ for _ in ()).throw(InferenceTimeoutError(f"{operation_name} timed out after {timeout_seconds} seconds")))
        timer.daemon = True
        timer.start()
        try:
            yield
        finally:
            timer.cancel()

def enforce_inference_timeout(func: Callable, timeout_seconds: float = 120.0):
    """
    Decorator to enforce a timeout on an inference function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        with timeout_context(timeout_seconds, f"Inference: {func.__name__}"):
            return func(*args, **kwargs)
    return wrapper

def signal_handler_factory(signum, frame):
    """Factory for signal handlers to be used with timeout_context if needed externally."""
    raise InferenceTimeoutError("Process interrupted by signal")

# Download with Retry
@retry_with_backoff(max_retries=5, initial_delay=2.0, exceptions=(requests.RequestException, ConnectionError, TimeoutError))
def safe_download_with_retry(url: str, dest_path: str, chunk_size: int = 8192) -> None:
    """
    Downloads a file from a URL with retry logic and progress logging.
    Raises DatasetDownloadError if download fails permanently.
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {url} to {dest_path}")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Download successful: {dest_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed for {url}: {e}")
        raise DatasetDownloadError(f"Failed to download {url}: {e}") from e

def run_inference_with_timeout(func: Callable, timeout_seconds: float = 120.0) -> Callable:
    """
    Wrapper to run an inference function with a hard timeout.
    """
    return enforce_inference_timeout(func, timeout_seconds)

def configure_retry_policy(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> Callable:
    """
    Factory function to create a retry decorator with specific configuration.
    Useful for injecting policy into specific modules.
    """
    return retry_with_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        exponential_base=exponential_base,
        jitter=jitter
    )

# Helper to compute SHA-256 for integrity checks (moved from ingestion if needed, but kept here for framework completeness)
def compute_sha256(file_path: str) -> str:
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_hash_state(hash_file: str, artifact_name: str, file_path: str) -> None:
    """Updates the state file with the hash of an artifact."""
    state_path = Path(hash_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    if state_path.exists():
        with open(state_path, 'r') as f:
            try:
                state = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state = {}
    else:
        state = {}
    
    if 'artifacts' not in state:
        state['artifacts'] = {}
    
    state['artifacts'][artifact_name] = {
        'path': str(file_path),
        'sha256': compute_sha256(file_path),
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
