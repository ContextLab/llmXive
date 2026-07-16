"""
Error handling framework for the plant defense prediction pipeline.

Provides centralized error handling, logging, and specific error raising
functions for the defined error codes: E-DATASET, E-PAIRING, E-TIMEOUT, E-POWER.
"""

import sys
import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path

from exceptions import (
    PipelineError,
    E_DATASET,
    E_PAIRING,
    E_TIMEOUT,
    E_POWER
)

# Configure module logger
logger = logging.getLogger(__name__)

# Timeout tracking
_start_time: Optional[float] = None
_timeout_limit_seconds: int = 14400  # 4 hours per FR-008

def set_timeout_limit(seconds: int) -> None:
    """Set the CPU time limit for the pipeline execution."""
    global _timeout_limit_seconds
    _timeout_limit_seconds = seconds

def start_timeout_monitor() -> None:
    """Start the CPU time monitor."""
    global _start_time
    _start_time = time.time()
    logger.info(f"Timeout monitor started. Limit: {_timeout_limit_seconds} seconds")

def check_timeout() -> bool:
    """
    Check if the elapsed CPU time exceeds the timeout limit.
    
    Returns:
        True if timeout exceeded, False otherwise.
    """
    if _start_time is None:
        return False
    
    elapsed = time.time() - _start_time
    if elapsed > _timeout_limit_seconds:
        logger.error(f"Timeout exceeded: {elapsed:.2f}s > {_timeout_limit_seconds}s")
        return True
    return False

def handle_error(
    error: Exception,
    log_file: Optional[Path] = None,
    exit_on_error: bool = True
) -> None:
    """
    Centralized error handler that logs and optionally exits.
    
    Args:
        error: The exception instance to handle
        log_file: Optional path to append error details
        exit_on_error: If True, terminate the program after logging
    """
    error_msg = str(error)
    error_code = getattr(error, 'error_code', 'E-UNKNOWN')
    
    # Log to console/logger
    logger.error(f"[{error_code}] {error_msg}")
    
    # Log to file if provided
    if log_file:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, 'a') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {error_code} | {error_msg}\n")
        except Exception as log_err:
            logger.warning(f"Failed to write error log to {log_file}: {log_err}")
    
    if exit_on_error:
        logger.critical("Pipeline terminated due to critical error.")
        sys.exit(1)

def raise_dataset_error(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise E_DATASET exception with optional context.
    
    Args:
        message: Human-readable error message
        context: Optional dict with additional details (e.g., accession_id, source_url)
    """
    if context:
        details = " | ".join([f"{k}={v}" for k, v in context.items()])
        full_message = f"{message} ({details})"
    else:
        full_message = message
    
    logger.critical(f"E-DATASET: {full_message}")
    raise E_DATASET(full_message)

def raise_pairing_error(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise E_PAIRING exception with optional context.
    
    Args:
        message: Human-readable error message
        context: Optional dict with pairing statistics (e.g., pairing_rate, n_matched, n_total)
    """
    if context:
        details = " | ".join([f"{k}={v}" for k, v in context.items()])
        full_message = f"{message} ({details})"
    else:
        full_message = message
    
    logger.critical(f"E-PAIRING: {full_message}")
    raise E_PAIRING(full_message)

def raise_timeout_error(message: str) -> None:
    """
    Raise E_TIMEOUT exception.
    
    Args:
        message: Human-readable error message
    """
    full_message = f"{message} (Timeout limit: {_timeout_limit_seconds}s)"
    logger.critical(f"E-TIMEOUT: {full_message}")
    raise E_TIMEOUT(full_message)

def raise_power_error(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Raise E_POWER exception with optional context.
    
    Args:
        message: Human-readable error message
        context: Optional dict with power analysis details (e.g., required_n, available_n, effect_size)
    """
    if context:
        details = " | ".join([f"{k}={v}" for k, v in context.items()])
        full_message = f"{message} ({details})"
    else:
        full_message = message
    
    logger.critical(f"E-POWER: {full_message}")
    raise E_POWER(full_message)
