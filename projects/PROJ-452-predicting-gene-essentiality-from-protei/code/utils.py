"""
Utility functions for the llmXive pipeline.

Provides logging setup, SHA256 checksumming, and exponential backoff helpers.
"""
import hashlib
import logging
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, List, Optional, TypeVar, Union

T = TypeVar('T')

def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the root logger with a standard format.
    
    Args:
        level: Logging level (default: INFO)
    """
    if logging.getLogger().handlers:
        # Logger already configured
        return

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(level)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry a function with exponential backoff on specified exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap in seconds.
        exceptions: Tuple of exception types to catch and retry on.
        
    Returns:
        Decorated function.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = base_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    logging.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)
            
            raise last_exception
        return wrapper
    return decorator

def safe_join(base: Union[str, Path], *paths: str) -> Path:
    """
    Safely join paths, preventing directory traversal attacks.
    
    Args:
        base: Base path.
        *paths: Path components to join.
        
    Returns:
        Joined Path object.
        
    Raises:
        ValueError: If the resulting path escapes the base directory.
    """
    base_path = Path(base)
    result = base_path.joinpath(*paths).resolve()
    
    if not str(result).startswith(str(base_path.resolve())):
        raise ValueError(f"Path traversal attempt detected: {result} is outside {base_path}")
    
    return result

def format_size(num_bytes: int) -> str:
    """
    Format a byte size into a human-readable string.
    
    Args:
        num_bytes: Size in bytes.
        
    Returns:
        Formatted string (e.g., "1.5 MB").
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"
