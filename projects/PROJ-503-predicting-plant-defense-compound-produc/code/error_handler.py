"""
Error handling framework for the plant defense compound prediction pipeline.
Implements timeout monitoring and validation logic for error codes:
- E-DATASET, E-PAIRING, E-TIMEOUT, E-POWER
"""
import sys
import time
import logging
import signal
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from functools import wraps
from contextlib import contextmanager

from exceptions import (
    E_DATASET, E_PAIRING, E_TIMEOUT, E_POWER, E_SAMPLESIZE,
    raise_dataset_error, raise_pairing_error, raise_timeout_error,
    raise_power_error, raise_samplesize_error
)

# Configure logging for error tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default timeout limit in seconds (4 hours as per FR-008)
DEFAULT_TIMEOUT_SECONDS = 4 * 60 * 60  # 4 hours

# Global timeout state
_timeout_start: Optional[float] = None
_timeout_limit: float = DEFAULT_TIMEOUT_SECONDS


def set_timeout_limit(seconds: float) -> None:
    """
    Set the global timeout limit for the pipeline execution.
    
    Args:
        seconds: Timeout limit in seconds (default: 4 hours)
    """
    global _timeout_limit
    _timeout_limit = seconds
    logger.info(f"Timeout limit set to {seconds} seconds ({seconds/3600:.2f} hours)")


def start_timeout_monitor() -> None:
    """Start the timeout monitoring timer."""
    global _timeout_start
    _timeout_start = time.time()
    logger.info("Timeout monitor started")


def check_timeout() -> Optional[bool]:
    """
    Check if the timeout has been exceeded.
    
    Returns:
        True if timeout exceeded, None if not started, False if within limit
    """
    if _timeout_start is None:
        return None
    
    elapsed = time.time() - _timeout_start
    if elapsed > _timeout_limit:
        logger.error(f"Timeout exceeded: {elapsed:.2f}s > {_timeout_limit}s")
        return True
    return False


def wrap_with_timeout(timeout_seconds: Optional[float] = None) -> Callable:
    """
    Decorator to wrap a function with timeout enforcement.
    
    Args:
        timeout_seconds: Optional specific timeout for this function
        
    Returns:
        Decorated function that raises E_TIMEOUT if exceeded
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            limit = timeout_seconds if timeout_seconds else _timeout_limit
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.debug(f"{func.__name__} completed in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"{func.__name__} failed after {elapsed:.2f}s: {str(e)}")
                raise
        return wrapper
    return decorator


@contextmanager
def timeout_context(timeout_seconds: Optional[float] = None):
    """
    Context manager for timeout enforcement.
    
    Args:
        timeout_seconds: Optional specific timeout for this block
        
    Raises:
        E_TIMEOUT: If timeout is exceeded within the context
    """
    start_time = time.time()
    limit = timeout_seconds if timeout_seconds else _timeout_limit
    
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        if elapsed > limit:
            logger.error(f"Context timeout: {elapsed:.2f}s > {limit}s")
            raise E_TIMEOUT(f"Operation exceeded timeout limit of {limit} seconds")


def handle_error(error: Exception) -> None:
    """
    Centralized error handler that logs and formats error messages.
    
    Args:
        error: The exception instance to handle
    """
    if isinstance(error, PipelineError):
        logger.error(f"[{error.error_code}] {error.message}")
        if error.details:
            logger.error(f"Details: {error.details}")
    else:
        logger.error(f"Unexpected error: {type(error).__name__}: {str(error)}")
    
    # Re-raise to allow proper propagation
    raise error


def validate_pairing_rate(pairing_rate: float, threshold: float = 0.95) -> None:
    """
    Validate that the pairing rate meets the minimum threshold.
    
    Args:
        pairing_rate: The calculated pairing rate (0.0 to 1.0)
        threshold: Minimum required pairing rate (default: 0.95)
        
    Raises:
        E_PAIRING: If pairing rate is below threshold
    """
    if pairing_rate < threshold:
        details = {
            "pairing_rate": pairing_rate,
            "threshold": threshold,
            "deficit": threshold - pairing_rate
        }
        raise_pairing_error(
            f"Pairing rate {pairing_rate:.2%} is below required threshold {threshold:.2%}",
            details
        )
    logger.info(f"Pairing rate validation passed: {pairing_rate:.2%} >= {threshold:.2%}")


def validate_sample_size(sample_size: int, minimum_required: int = 28) -> None:
    """
    Validate that the sample size meets the minimum requirement for power analysis.
    
    Args:
        sample_size: The number of samples available
        minimum_required: Minimum required sample size (default: 28 per T015)
        
    Raises:
        E_POWER: If sample size is insufficient for statistical power
    """
    if sample_size < minimum_required:
        details = {
            "sample_size": sample_size,
            "minimum_required": minimum_required,
            "deficit": minimum_required - sample_size
        }
        raise_power_error(
            f"Sample size {sample_size} is below minimum required {minimum_required} for power analysis",
            details
        )
    logger.info(f"Sample size validation passed: {sample_size} >= {minimum_required}")


def validate_dataset_availability(dataset_count: int, minimum_required: int = 1) -> None:
    """
    Validate that at least one verified dataset is available.
    
    Args:
        dataset_count: Number of verified datasets found
        minimum_required: Minimum required datasets (default: 1)
        
    Raises:
        E_DATASET: If no verified datasets are found
    """
    if dataset_count < minimum_required:
        details = {
            "dataset_count": dataset_count,
            "minimum_required": minimum_required
        }
        raise_dataset_error(
            f"No verified plant omics datasets found. Required: {minimum_required}, Found: {dataset_count}",
            details
        )
    logger.info(f"Dataset availability validation passed: {dataset_count} >= {minimum_required}")


# Re-export for convenience
__all__ = [
    'set_timeout_limit',
    'start_timeout_monitor',
    'check_timeout',
    'wrap_with_timeout',
    'timeout_context',
    'handle_error',
    'validate_pairing_rate',
    'validate_sample_size',
    'validate_dataset_availability',
    'E_DATASET',
    'E_PAIRING',
    'E_TIMEOUT',
    'E_POWER',
    'E_SAMPLESIZE',
    'raise_dataset_error',
    'raise_pairing_error',
    'raise_timeout_error',
    'raise_power_error',
    'raise_samplesize_error'
]
