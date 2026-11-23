import hashlib
import logging
import time
import random
import os
from functools import wraps
from typing import Callable, Any, Optional

# Standard library imports only
import sys
import numpy as np

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up logging configuration.
    
    Args:
        log_file: Optional path to a log file. If provided, logs are written to both console and file.
        level: Logging level (default: INFO).
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger('root')
    logger.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def compute_sha256(file_path: str) -> str:
    """
    Computes the SHA256 hash of a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def exponential_backoff(retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Decorator for retrying a function with exponential backoff.
    
    Args:
        retries: Maximum number of attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
    
    Returns:
        Decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:
                        raise e
                    logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)
        return wrapper
    return decorator

def safe_join(base: str, *paths: str) -> str:
    """
    Safely joins paths, preventing directory traversal attacks.
    
    Args:
        base: Base directory path.
        *paths: Relative path components.
    
    Returns:
        Safe joined path.
    
    Raises:
        ValueError: If the resulting path is outside the base directory.
    """
    full_path = os.path.join(base, *paths)
    real_base = os.path.realpath(base)
    real_path = os.path.realpath(full_path)
    
    if not real_path.startswith(real_base + os.sep) and real_path != real_base:
        raise ValueError(f"Path '{full_path}' is outside base directory '{base}'")
    return full_path

def format_size(num: float) -> str:
    """
    Formats a number of bytes into a human-readable string.
    
    Args:
        num: Number of bytes.
    
    Returns:
        Human-readable size string (e.g., "1.5 MB").
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return f"{num:.2f} {unit}"
        num /= 1024.0
    return f"{num:.2f} PB"

def set_deterministic_seed(seed: int = 42) -> None:
    """
    Sets deterministic random seeds for reproducibility.
    
    This function sets the seed for:
    - Python's built-in random module
    - NumPy's random module
    - PYTHONHASHSEED environment variable (for hash randomization)
    
    Args:
        seed: Integer seed value (default: 42).
    """
    logging.info(f"Setting deterministic random seed to {seed} for reproducibility")
    
    # Set Python random seed
    random.seed(seed)
    
    # Set NumPy random seed
    np.random.seed(seed)
    
    # Set PYTHONHASHSEED environment variable
    # Note: This must be set before Python starts for full effect, but setting it here
    # ensures it is available for any subprocesses spawned later
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_deterministic_seed() -> Optional[int]:
    """
    Retrieves the current deterministic seed from environment or defaults.
    
    Returns:
        The seed integer if set, None otherwise.
    """
    hash_seed = os.environ.get('PYTHONHASHSEED')
    if hash_seed:
        try:
            return int(hash_seed)
        except ValueError:
            return None
    return None

def reset_random_state() -> None:
    """
    Resets the random state to a known default (seed=42).
    
    Useful for ensuring consistent behavior after tests or partial runs.
    """
    set_deterministic_seed(42)
    logging.info("Random state reset to default seed (42)")