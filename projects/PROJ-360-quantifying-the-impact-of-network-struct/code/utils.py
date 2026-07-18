"""
Utility functions for the project.

Includes:
- Logging setup.
- Retry logic with exponential backoff.
- Seed pinning for reproducibility.
"""

import logging
import random
import time
import os
from typing import Callable, TypeVar, List, Any, Optional
from functools import wraps
from pathlib import Path

# Ensure results directory exists for logs
LOG_DIR = Path("results")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup a logger with a file handler and console handler.

    Args:
        name: Logger name (usually __name__).
        log_file: Relative path to log file.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates in some environments
    if logger.handlers:
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path)
        fh.setFormatter(formatter)
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    return logger

def pin_seed(seed: int = 42):
    """
    Pin random seeds for reproducibility.

    Args:
        seed: Random seed integer.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # If numpy is used, it should be seeded there too, but we handle core random here.
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

T = TypeVar('T')

def retry_with_exponential_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    backoff_multiplier: float = 2.0,
    logger: Optional[logging.Logger] = None
) -> Callable[..., T]:
    """
    Decorator to retry a function with exponential backoff.

    Args:
        func: The function to wrap.
        max_retries: Maximum number of retry attempts.
        initial_backoff: Initial backoff time in seconds.
        backoff_multiplier: Multiplier for backoff time.
        logger: Optional logger for retry messages.

    Returns:
        Wrapped function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        backoff = initial_backoff
        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    if logger:
                        logger.warning(
                            f"Attempt {attempt} failed: {e}. Retrying in {backoff:.1f}s..."
                        )
                    time.sleep(backoff)
                    backoff *= backoff_multiplier
                else:
                    if logger:
                        logger.error(f"Attempt {attempt} failed: {e}. No more retries.")

        raise last_exception

    return wrapper

def fetch_with_retry(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    backoff_multiplier: float = 2.0,
    logger: Optional[logging.Logger] = None
) -> T:
    """
    Function-level retry wrapper (non-decorator style) for one-off calls.
    Useful when we need to retry a specific call without decorating the function.

    Args:
        func: Callable to execute.
        max_retries: Max retry attempts.
        initial_backoff: Initial backoff seconds.
        backoff_multiplier: Backoff multiplier.
        logger: Logger instance.

    Returns:
        Result of the function.

    Raises:
        The last exception encountered if all retries fail.
    """
    backoff = initial_backoff
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                if logger:
                    logger.warning(
                        f"Attempt {attempt} failed: {e}. Retrying in {backoff:.1f}s..."
                    )
                time.sleep(backoff)
                backoff *= backoff_multiplier
            else:
                if logger:
                    logger.error(f"Attempt {attempt} failed: {e}. No more retries.")

    raise last_exception