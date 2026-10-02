"""
Utility functions for the llmXive pipeline.

Provides logging setup, SHA256 checksumming, exponential backoff helpers,
and deterministic random seed management for reproducibility.
"""
import hashlib
import logging
import time
import random
import os
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

def set_deterministic_seed(seed: int = 42) -> None:
    """
    Set deterministic random seeds for full reproducibility of streaming 
    and sampling processes across runs.
    
    This function initializes seeds for:
    - Python's built-in random module
    - NumPy's random number generator (if available)
    - The OS-level random seed environment variable (for subprocess reproducibility)
    
    Args:
        seed: Integer seed value (default: 42). Must be non-negative.
            
    Raises:
        ValueError: If seed is negative.
    """
    if seed < 0:
        raise ValueError(f"Seed must be non-negative, got {seed}")
    
    logging.info(f"Setting deterministic random seed to {seed} for reproducibility")
    
    # Set Python random seed
    random.seed(seed)
    logging.debug(f"Python random module seeded with {seed}")
    
    # Set NumPy random seed if available
    try:
        import numpy as np
        np.random.seed(seed)
        logging.debug(f"NumPy random module seeded with {seed}")
    except ImportError:
        logging.warning("NumPy not available; skipping NumPy seed initialization")
    
    # Set environment variable for subprocess reproducibility
    os.environ['PYTHONHASHSEED'] = str(seed)
    os.environ['RANDOM_SEED'] = str(seed)
    logging.debug(f"Environment variables PYTHONHASHSEED and RANDOM_SEED set to {seed}")

def get_deterministic_seed() -> int:
    """
    Retrieve the current deterministic seed from environment or return default.
    
    Returns:
        The seed integer currently in use, or 42 if not set.
    """
    return int(os.environ.get('RANDOM_SEED', os.environ.get('PYTHONHASHSEED', '42')))

def reset_random_state() -> None:
    """
    Reset all random number generators to an undefined state (non-deterministic).
    
    Useful for testing scenarios where reproducibility is not required.
    """
    random.seed()
    try:
        import numpy as np
        np.random.seed(None)
    except ImportError:
        pass
    
    if 'RANDOM_SEED' in os.environ:
        del os.environ['RANDOM_SEED']
    if 'PYTHONHASHSEED' in os.environ:
        del os.environ['PYTHONHASHSEED']
    
    logging.info("Random state reset to non-deterministic mode")