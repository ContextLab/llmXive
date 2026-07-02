"""
Error handling utilities for the plant defense prediction pipeline.

Provides functions for logging and raising pipeline errors with proper
error codes and context information.
"""
import sys
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from exceptions import PipelineError, E_DATASET, E_PAIRING, E_TIMEOUT, E_POWER

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    exit_on_error: bool = True
) -> None:
    """
    Handle an error by logging it and optionally exiting.
    
    Parameters:
    -----------
    error : Exception
        The exception to handle.
    context : Optional[Dict[str, Any]]
        Additional context information for the error.
    exit_on_error : bool
        Whether to exit the program after handling the error.
    """
    logger.error(f"Error occurred: {error}")
    if context:
        logger.error(f"Context: {context}")
    
    if exit_on_error:
        sys.exit(1)

def raise_dataset_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise an E_DATASET exception with the given message and details.
    
    Parameters:
    -----------
    message : str
        Error message.
    details : Optional[Dict[str, Any]]
        Additional error details.
    """
    raise E_DATASET(message, details=details)

def raise_pairing_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise an E_PAIRING exception with the given message and details.
    
    Parameters:
    -----------
    message : str
        Error message.
    details : Optional[Dict[str, Any]]
        Additional error details.
    """
    raise E_PAIRING(message, details=details)

def raise_timeout_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise an E_TIMEOUT exception with the given message and details.
    
    Parameters:
    -----------
    message : str
        Error message.
    details : Optional[Dict[str, Any]]
        Additional error details.
    """
    raise E_TIMEOUT(message, details=details)

def raise_power_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise an E_POWER exception with the given message and details.
    
    Parameters:
    -----------
    message : str
        Error message.
    details : Optional[Dict[str, Any]]
        Additional error details.
    """
    raise E_POWER(message, details=details)

def check_timeout(elapsed_time: float, timeout_seconds: float = 14400) -> None:
    """
    Check if elapsed time exceeds timeout threshold.
    
    Parameters:
    -----------
    elapsed_time : float
        Elapsed CPU time in seconds.
    timeout_seconds : float
        Maximum allowed time in seconds (default 4 hours = 14400s).
        
    Raises:
    -------
    E_TIMEOUT
        If elapsed time exceeds timeout threshold.
    """
    if elapsed_time > timeout_seconds:
        raise_timeout_error(
            f"CPU time limit exceeded: {elapsed_time:.2f}s > {timeout_seconds}s"
        )
