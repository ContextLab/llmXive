"""
Error handling framework for the plant defense compound prediction pipeline.
Implements error codes (E-DATASET, E-PAIRING, E-TIMEOUT, E-POWER) and
provides utility functions for error management and timeout monitoring.
"""
import sys
import time
import logging
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from exceptions import (
    PipelineError,
    E_DATASET,
    E_PAIRING,
    E_TIMEOUT,
    E_POWER
)


# Configure logger
logger = logging.getLogger(__name__)


# Global timeout limit (seconds) - default 4 hours as per FR-008
_TIMEOUT_LIMIT_SECONDS = 14400
_start_time: Optional[float] = None


def set_timeout_limit(seconds: int) -> None:
    """
    Set the global timeout limit for the pipeline.
    
    Args:
        seconds: Maximum allowed CPU time in seconds (default: 14400 for 4 hours)
    """
    global _TIMEOUT_LIMIT_SECONDS
    _TIMEOUT_LIMIT_SECONDS = seconds
    logger.info(f"Timeout limit set to {_TIMEOUT_LIMIT_SECONDS} seconds")


def start_timeout_monitor() -> None:
    """
    Start the timeout monitoring timer.
    Should be called at the beginning of the pipeline execution.
    """
    global _start_time
    _start_time = time.time()
    logger.info("Timeout monitor started")


def check_timeout() -> bool:
    """
    Check if the elapsed time exceeds the timeout limit.
    
    Returns:
        True if timeout has been exceeded, False otherwise.
    """
    if _start_time is None:
        return False
    
    elapsed = time.time() - _start_time
    if elapsed > _TIMEOUT_LIMIT_SECONDS:
        logger.error(f"Timeout exceeded: {elapsed:.2f}s > {_TIMEOUT_LIMIT_SECONDS}s")
        return True
    return False


def handle_error(error: PipelineError) -> None:
    """
    Handle a pipeline error by logging and exiting.
    
    Args:
        error: The PipelineError instance to handle.
    """
    logger.error(f"Pipeline error occurred: {error.error_code} - {error.message}")
    if error.details:
        logger.error(f"Error details: {error.details}")
    
    # Log to stderr for visibility
    print(f"ERROR: {error.error_code} - {error.message}", file=sys.stderr)
    
    # Exit with non-zero status
    sys.exit(1)


def raise_dataset_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise an E_DATASET error for dataset-related failures.
    
    Args:
        message: Description of the dataset failure.
        details: Optional dictionary with additional error context.
    """
    error = E_DATASET(message, details)
    logger.critical(f"Dataset error: {message}")
    if details:
        logger.critical(f"Details: {details}")
    raise error


def raise_pairing_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise an E_PAIRING error for sample pairing failures.
    
    Args:
        message: Description of the pairing failure.
        details: Optional dictionary with additional error context.
    """
    error = E_PAIRING(message, details)
    logger.critical(f"Pairing error: {message}")
    if details:
        logger.critical(f"Details: {details}")
    raise error


def raise_timeout_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise an E_TIMEOUT error when computational budget is exceeded.
    
    Args:
        message: Description of the timeout condition.
        details: Optional dictionary with additional error context.
    """
    error = E_TIMEOUT(message, details)
    logger.critical(f"Timeout error: {message}")
    if details:
        logger.critical(f"Details: {details}")
    raise error


def raise_power_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise an E_POWER error when power analysis fails (n < 28).
    
    Args:
        message: Description of the power analysis failure.
        details: Optional dictionary with additional error context.
    """
    error = E_POWER(message, details)
    logger.critical(f"Power analysis error: {message}")
    if details:
        logger.critical(f"Details: {details}")
    raise error


def wrap_with_timeout(func: Callable) -> Callable:
    """
    Decorator to wrap a function with timeout monitoring.
    
    Args:
        func: The function to wrap.
        
    Returns:
        Wrapped function that checks timeout before execution.
    """
    def wrapper(*args, **kwargs):
        if check_timeout():
            raise_timeout_error(
                "Pipeline execution exceeded time limit",
                {"limit_seconds": _TIMEOUT_LIMIT_SECONDS}
            )
        return func(*args, **kwargs)
    return wrapper
