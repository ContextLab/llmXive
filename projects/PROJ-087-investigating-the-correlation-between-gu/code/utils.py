import os
import hashlib
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable, TypeVar, List

logger = logging.getLogger(__name__)

# Type variable for generic retry function
T = TypeVar('T')

def ensure_directory(path: str) -> None:
    """Create directory and all parents if they don't exist."""
    os.makedirs(path, exist_ok=True)
    logger.info(f"Ensured directory exists: {path}")

def calculate_file_checksum(file_path: str, algorithm: str = "md5") -> Optional[str]:
    """
    Calculate checksum of a file for validation.
    Returns None if file doesn't exist or cannot be read.
    """
    file_obj = Path(file_path)
    if not file_obj.exists():
        logger.error(f"File not found for checksum: {file_path}")
        return None

    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate checksum for {file_path}: {e}")
        return None

def validate_checksum(file_path: str, expected_checksum: str, algorithm: str = "md5") -> bool:
    """
    Validate a file's checksum against an expected value.
    Returns True if valid, False otherwise.
    """
    actual_checksum = calculate_file_checksum(file_path, algorithm)
    if actual_checksum is None:
        return False
    
    is_valid = actual_checksum == expected_checksum
    if not is_valid:
        logger.error(
            f"Checksum mismatch for {file_path}. "
            f"Expected: {expected_checksum}, Got: {actual_checksum}"
        )
    else:
        logger.info(f"Checksum validation passed for {file_path}")
    return is_valid

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Configure logging for the application."""
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )

def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable[..., T]:
    """
    Decorator to retry a function with exponential backoff on specified exceptions.
    
    Args:
        func: The function to wrap.
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay in seconds before first retry.
        backoff_factor: Multiplier for delay after each retry.
        exceptions: Tuple of exception classes to catch and retry on.
    
    Returns:
        Wrapped function with retry logic.
    """
    def wrapper(*args, **kwargs) -> T:
        delay = initial_delay
        last_exception: Optional[Exception] = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt == max_retries:
                    logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                    raise
                
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
                delay *= backoff_factor
        
        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in retry logic")

    return wrapper

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning a default value if division by zero occurs.
    
    Args:
        numerator: The numerator.
        denominator: The denominator.
        default: Value to return if division by zero occurs.
    
    Returns:
        Result of division or default value.
    """
    if denominator == 0:
        logger.warning(f"Division by zero attempted: {numerator} / {denominator}. Returning default: {default}")
        return default
    return numerator / denominator

def log_execution_time(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to log the execution time of a function.
    
    Args:
        func: The function to wrap.
    
    Returns:
        Wrapped function with timing logs.
    """
    def wrapper(*args, **kwargs) -> T:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            elapsed = end_time - start_time
            logger.info(f"Function {func.__name__} executed in {elapsed:.4f} seconds")
    
    return wrapper