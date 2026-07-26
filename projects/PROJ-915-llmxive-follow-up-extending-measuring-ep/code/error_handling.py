"""
Error handling framework for dataset download retries and inference timeouts.

This module provides robust error handling mechanisms including:
- Custom exception classes for specific failure modes
- Retry logic with exponential backoff for transient failures
- Timeout enforcement for inference operations
- Signal-based interruption handling
- Safe download utilities with checksum verification
"""
import time
import logging
import signal
import sys
import os
import hashlib
from functools import wraps
from typing import Callable, Optional, Any, Tuple
from pathlib import Path
import threading
import concurrent.futures

# Configure logging for this module
logger = logging.getLogger(__name__)

# ============================================================================
# Custom Exception Classes
# ============================================================================

class InferenceTimeoutError(Exception):
    """Raised when an inference operation exceeds the allowed timeout."""
    def __init__(self, message: str = "Inference operation timed out", prompt_id: Optional[str] = None):
        self.prompt_id = prompt_id
        super().__init__(message)

class DatasetDownloadError(Exception):
    """Raised when dataset download fails after all retry attempts."""
    def __init__(self, message: str = "Dataset download failed", dataset_name: Optional[str] = None, attempt: int = 0):
        self.dataset_name = dataset_name
        self.attempt = attempt
        super().__init__(message)

class RetryExhaustedError(Exception):
    """Raised when retry attempts are exhausted for a transient operation."""
    def __init__(self, message: str = "Retry attempts exhausted", last_exception: Optional[Exception] = None):
        self.last_exception = last_exception
        super().__init__(message)

# ============================================================================
# Retry Logic with Exponential Backoff
# ============================================================================

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions_to_retry: Tuple[type, ...] = (ConnectionError, TimeoutError, OSError)
) -> Callable:
    """
    Decorator that adds retry logic with exponential backoff to a function.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to delays
        exceptions_to_retry: Tuple of exception types that should trigger a retry
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions_to_retry as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Retry exhausted for {func.__name__} after {max_retries + 1} attempts: {str(e)}"
                        )
                        raise RetryExhaustedError(
                            f"Retry exhausted for {func.__name__} after {max_retries + 1} attempts",
                            last_exception=e
                        ) from e
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter if enabled
                    if jitter:
                        import random
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                        f"Retrying in {delay:.2f}s: {str(e)}"
                    )
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            raise RetryExhaustedError(
                f"Retry exhausted for {func.__name__}",
                last_exception=last_exception
            )
        
        return wrapper
    return decorator

# ============================================================================
# Timeout Context and Enforcement
# ============================================================================

class timeout_context:
    """
    Context manager that enforces a timeout on a block of code.
    Uses threading to interrupt execution if timeout is exceeded.
    """
    def __init__(self, timeout_seconds: float, exception_class: type = InferenceTimeoutError):
        self.timeout_seconds = timeout_seconds
        self.exception_class = exception_class
        self._timer = None
        self._timed_out = False

    def _timeout_handler(self):
        """Handler called when timeout is exceeded."""
        self._timed_out = True
        raise self.exception_class(f"Operation timed out after {self.timeout_seconds} seconds")

    def __enter__(self):
        self._timer = threading.Timer(self.timeout_seconds, self._timeout_handler)
        self._timer.daemon = True
        self._timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._timer:
            self._timer.cancel()
        # Don't suppress exceptions
        return False

def enforce_inference_timeout(
    func: Callable,
    timeout_seconds: float
) -> Callable:
    """
    Decorator that enforces a timeout on an inference function.
    
    Args:
        func: The inference function to wrap
        timeout_seconds: Maximum allowed execution time
    
    Returns:
        Wrapped function with timeout enforcement
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        with timeout_context(timeout_seconds, InferenceTimeoutError):
            return func(*args, **kwargs)
    return wrapper

def run_inference_with_timeout(
    inference_func: Callable,
    prompt: str,
    timeout_seconds: float,
    *args,
    **kwargs
) -> Any:
    """
    Runs an inference function with a hard timeout.
    
    Args:
        inference_func: The function to execute
        prompt: The input prompt
        timeout_seconds: Maximum execution time
        *args, **kwargs: Additional arguments to pass to the function
    
    Returns:
        Result of the inference function
    
    Raises:
        InferenceTimeoutError: If the operation exceeds the timeout
    """
    def run_with_prompt():
        return inference_func(prompt, *args, **kwargs)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_with_prompt)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            raise InferenceTimeoutError(
                f"Inference timed out after {timeout_seconds} seconds for prompt: {prompt[:50]}..."
            )

# ============================================================================
# Signal Handler for Graceful Interruption
# ============================================================================

def signal_handler_factory(timeout_seconds: float = 300) -> Callable:
    """
    Creates a signal handler that enforces a global timeout for the pipeline.
    
    Args:
        timeout_seconds: Maximum total runtime before forcing exit
    
    Returns:
        Signal handler function
    """
    start_time = time.time()
    
    def handler(signum, frame):
        elapsed = time.time() - start_time
        logger.error(
            f"Pipeline exceeded maximum runtime of {timeout_seconds}s "
            f"(elapsed: {elapsed:.2f}s). Forcing exit."
        )
        sys.exit(1)
    
    return handler

def configure_signal_handler(timeout_seconds: float = 300):
    """
    Configures a signal handler for the pipeline timeout.
    
    Args:
        timeout_seconds: Maximum total runtime before forcing exit
    """
    handler = signal_handler_factory(timeout_seconds)
    
    # Register for SIGALRM (Unix) or SIGINT (Ctrl+C)
    try:
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout_seconds)
        logger.info(f"Configured pipeline timeout: {timeout_seconds}s (SIGALRM)")
    except AttributeError:
        # Windows doesn't support SIGALRM
        signal.signal(signal.SIGINT, handler)
        logger.info(f"Configured pipeline timeout: {timeout_seconds}s (SIGINT only on Windows)")

# ============================================================================
# Safe Download with Retry
# ============================================================================

@retry_with_backoff(
    max_retries=5,
    base_delay=2.0,
    max_delay=60.0,
    exceptions_to_retry=(ConnectionError, TimeoutError, OSError, DatasetDownloadError)
)
def safe_download_with_retry(
    url: str,
    output_path: str,
    chunk_size: int = 8192,
    timeout: float = 30.0
) -> str:
    """
    Safely downloads a file from a URL with retry logic and progress tracking.
    
    Args:
        url: URL to download from
        output_path: Local path to save the file
        chunk_size: Size of chunks to read during download
        timeout: Request timeout in seconds
    
    Returns:
        Path to the downloaded file
    
    Raises:
        DatasetDownloadError: If download fails after all retries
    """
    import urllib.request
    import urllib.error
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {url} to {output_path}")
    
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; llmXive Research Pipeline)')
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            total_size = int(response.getheader('Content-Length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Log progress every 10%
                    if total_size > 0 and downloaded % (total_size // 10) < chunk_size:
                        progress = (downloaded / total_size) * 100
                        logger.debug(f"Download progress: {progress:.1f}%")
        
        logger.info(f"Successfully downloaded {output_path.name} ({downloaded} bytes)")
        return str(output_path)
        
    except urllib.error.URLError as e:
        raise DatasetDownloadError(
            f"Failed to download from {url}: {str(e)}",
            dataset_name=url.split('/')[-1]
        ) from e
    except Exception as e:
        raise DatasetDownloadError(
            f"Unexpected error downloading {url}: {str(e)}",
            dataset_name=url.split('/')[-1]
        ) from e

# ============================================================================
# Checksum Utilities
# ============================================================================

def compute_sha256(file_path: str) -> str:
    """
    Computes the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
    
    Returns:
        Hexadecimal SHA-256 hash string
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

# ============================================================================
# Configuration for Retry Policies
# ============================================================================

def configure_retry_policy(
    dataset_download_retries: int = 5,
    inference_timeout_seconds: float = 120.0,
    pipeline_timeout_seconds: float = 300.0
) -> dict:
    """
    Configures global retry and timeout policies for the pipeline.
    
    Args:
        dataset_download_retries: Number of retry attempts for downloads
        inference_timeout_seconds: Timeout per inference operation
        pipeline_timeout_seconds: Total pipeline runtime limit
    
    Returns:
        Configuration dictionary
    """
    config = {
        'dataset_download_retries': dataset_download_retries,
        'inference_timeout_seconds': inference_timeout_seconds,
        'pipeline_timeout_seconds': pipeline_timeout_seconds
    }
    
    logger.info(
        f"Configured error handling: "
        f"download_retries={dataset_download_retries}, "
        f"inference_timeout={inference_timeout_seconds}s, "
        f"pipeline_timeout={pipeline_timeout_seconds}s"
    )
    
    return config

# ============================================================================
# State Management for Hash Tracking
# ============================================================================

def update_hash_state(
    state_file: str,
    artifact_name: str,
    file_path: str
) -> None:
    """
    Updates the artifact hash state file with a new checksum.
    
    Args:
        state_file: Path to the state YAML file
        artifact_name: Name of the artifact
        file_path: Path to the artifact file
    """
    import yaml
    
    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create new
    if state_path.exists():
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}
    
    # Compute and store hash
    file_hash = compute_sha256(file_path)
    state[artifact_name] = {
        'path': file_path,
        'sha256': file_hash,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }
    
    # Write updated state
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated hash state for {artifact_name}: {file_hash[:16]}...")