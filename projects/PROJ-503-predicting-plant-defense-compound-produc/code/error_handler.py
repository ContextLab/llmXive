"""
Error handling framework for the plant defense compound prediction pipeline.

Implements error codes E-DATASET, E-PAIRING, E-TIMEOUT, and E-POWER.
Provides utilities for timeout management, error logging, and graceful failure.
"""
import sys
import time
import logging
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from functools import wraps
import signal

from exceptions import (
    PipelineError,
    E_DATASET,
    E_PAIRING,
    E_TIMEOUT,
    E_POWER
)

# Configure logging
logger = logging.getLogger(__name__)

# Global timeout limit (in seconds) - default 4 hours
GLOBAL_TIMEOUT_LIMIT = 4 * 60 * 60  # 14400 seconds
_timeout_start_time: Optional[float] = None
_timeout_limit: float = GLOBAL_TIMEOUT_LIMIT


def set_timeout_limit(seconds: float) -> None:
    """
    Set the global timeout limit for the pipeline.
    
    Args:
        seconds: Timeout limit in seconds
    """
    global _timeout_limit
    _timeout_limit = seconds
    logger.info(f"Timeout limit set to {seconds} seconds ({seconds/3600:.2f} hours)")


def start_timeout_monitor() -> None:
    """
    Start the timeout monitoring timer.
    
    Must be called at the beginning of the pipeline execution.
    """
    global _timeout_start_time
    _timeout_start_time = time.time()
    logger.info("Timeout monitor started")

def check_timeout() -> None:
    """
    Check if the timeout limit has been exceeded.
    
    Raises:
        E_TIMEOUT: If elapsed time exceeds the limit
    """
    if _timeout_start_time is None:
        return
    
    elapsed = time.time() - _timeout_start_time
    if elapsed > _timeout_limit:
        error = E_TIMEOUT(
            f"Pipeline execution exceeded time limit of {_timeout_limit} seconds",
            details={
                "elapsed_seconds": elapsed,
                "limit_seconds": _timeout_limit,
                "elapsed_hours": elapsed / 3600
            }
        )
        logger.error(f"TIMEOUT: {error}")
        raise error


def wrap_with_timeout(timeout_seconds: Optional[float] = None):
    """
    Decorator to enforce timeout on a function.
    
    Args:
        timeout_seconds: Optional timeout override for this function
        
    Returns:
        Decorated function that raises E_TIMEOUT if exceeded
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_start = time.time()
            limit = timeout_seconds if timeout_seconds is not None else _timeout_limit
            
            def timeout_handler(signum, frame):
                raise E_TIMEOUT(
                    f"Function {func.__name__} exceeded timeout of {limit} seconds",
                    details={
                        "function": func.__name__,
                        "limit_seconds": limit
                    }
                )
            
            # Set signal handler (Unix only)
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(limit))
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorator


def handle_error(error: PipelineError, exit_on_error: bool = True) -> None:
    """
    Handle a pipeline error with logging and optional exit.
    
    Args:
        error: The PipelineError instance to handle
        exit_on_error: If True, exit the program after logging
    """
    logger.critical(f"ERROR [{error.code}]: {error.message}")
    if error.details:
        logger.critical(f"Error details: {error.details}")
    
    if exit_on_error:
        logger.critical(f"Pipeline aborted due to {error.code}")
        sys.exit(1)

def raise_dataset_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise an E_DATASET error.
    
    Args:
        message: Error message
        details: Optional dictionary of error details
        
    Raises:
        E_DATASET: Always
    """
    error = E_DATASET(message, details)
    logger.error(f"Dataset error: {error}")
    raise error

def raise_pairing_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise an E_PAIRING error.
    
    Args:
        message: Error message
        details: Optional dictionary of error details
        
    Raises:
        E_PAIRING: Always
    """
    error = E_PAIRING(message, details)
    logger.error(f"Pairing error: {error}")
    raise error

def raise_timeout_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise an E_TIMEOUT error.
    
    Args:
        message: Error message
        details: Optional dictionary of error details
        
    Raises:
        E_TIMEOUT: Always
    """
    error = E_TIMEOUT(message, details)
    logger.error(f"Timeout error: {error}")
    raise error

def raise_power_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise an E_POWER error.
    
    Args:
        message: Error message
        details: Optional dictionary of error details
        
    Raises:
        E_POWER: Always
    """
    error = E_POWER(message, details)
    logger.error(f"Power analysis error: {error}")
    raise error


def validate_pairing_rate(rate: float, threshold: float = 0.95, min_samples: int = 28) -> None:
    """
    Validate pairing rate and sample size, raising E_PAIRING if requirements not met.
    
    Args:
        rate: Pairing rate (0.0 to 1.0)
        threshold: Minimum required pairing rate (default 0.95)
        min_samples: Minimum required sample size (default 28)
        
    Raises:
        E_PAIRING: If rate < threshold or samples < min_samples
    """
    if rate < threshold:
        raise_pairing_error(
            f"Pairing rate {rate:.2%} is below required threshold {threshold:.2%}",
            details={"pairing_rate": rate, "threshold": threshold}
        )

def validate_sample_size(n: int, min_required: int = 28) -> None:
    """
    Validate sample size, raising E_POWER if insufficient.
    
    Args:
        n: Available sample size
        min_required: Minimum required sample size (default 28)
        
    Raises:
        E_POWER: If n < min_required
    """
    if n < min_required:
        raise_power_error(
            f"Sample size {n} is below minimum required {min_required} for statistical power",
            details={"available_n": n, "required_n": min_required}
        )
