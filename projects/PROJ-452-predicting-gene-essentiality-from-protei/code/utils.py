"""
Utility functions for the gene essentiality pipeline.

Provides:
- Logging setup
- SHA256 checksumming
- Exponential backoff helpers for API retries
"""
import hashlib
import logging
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, List, Optional, TypeVar, Union

# Type alias for the backoff function
T = TypeVar('T')

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    format_str: Optional[str] = None
) -> logging.Logger:
    """
    Configure the root logger for the pipeline.
    
    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If None, only logs to console.
        format_str: Optional custom format string. Defaults to a standard 
                    pipeline format including timestamp, level, and message.
                    
    Returns:
        The root logger instance.
    """
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates on re-calls
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(format_str))
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(format_str))
        root_logger.addHandler(file_handler)
    
    return root_logger


def compute_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute the SHA256 hash of a file's contents.
    
    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read at a time (default 8KB).
                    
    Returns:
        Hexadecimal string of the SHA256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def exponential_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry a function with exponential backoff on specified exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds between retries.
        max_delay: Maximum delay cap in seconds.
        exceptions: Tuple of exception types to catch and retry on.
                    
    Returns:
        A decorator function.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = base_delay
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logging.getLogger(func.__module__).error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    logger = logging.getLogger(func.__module__)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)
            
            # Should not be reached, but required for type checking
            raise last_exception # type: ignore
        return wrapper
    return decorator


def safe_join(*paths: Union[str, Path]) -> Path:
    """
    Safely join path components, ensuring the result is a Path object.
    
    Args:
        *paths: Path components to join.
        
    Returns:
        A unified Path object.
    """
    return Path(*paths)


def format_size(size_bytes: int) -> str:
    """
    Format a byte size into a human-readable string (KB, MB, GB).
    
    Args:
        size_bytes: Size in bytes.
        
    Returns:
        Formatted string (e.g., "1.5 MB").
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"