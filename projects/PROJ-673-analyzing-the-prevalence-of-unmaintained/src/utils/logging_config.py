"""
Logging infrastructure for tracking API success/failure rates (FR-009).

This module provides a configurable logging setup that:
1. Initializes a secure logger (no secrets in logs)
2. Tracks API success/failure events via a dedicated metric logger
3. Provides a helper to log API interactions with redacted sensitive data
"""

import logging
import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path

# Import security utilities to ensure no secrets are logged
from src.utils.security import secure_logger, sanitize_value, ensure_no_secrets_in_log_record

# Constants
DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "api_metrics.log"
API_METRIC_LOGGER_NAME = "api_metrics"
GENERAL_LOGGER_NAME = "api_client"

# Ensure log directory exists
LOG_DIR.mkdir(exist_ok=True)

# Global registry for tracking metrics in memory (for aggregation by api_metrics.py)
_metric_registry: Dict[str, Dict[str, int]] = {
    "success": 0,
    "failure": 0,
    "total": 0
}

def get_api_logger(name: str = GENERAL_LOGGER_NAME) -> logging.Logger:
    """
    Get a configured logger for API clients.
    
    This logger uses a secure formatter and ensures no secrets are logged.
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, DEFAULT_LOG_LEVEL, logging.INFO))
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Apply security sanitization
    secure_logger(logger)
    
    return logger

def get_metric_logger() -> logging.Logger:
    """
    Get the dedicated logger for API success/failure metrics.
    
    This logger is specifically for tracking rates required by FR-009 and SC-004.
    """
    logger = logging.getLogger(API_METRIC_LOGGER_NAME)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # File handler for metrics
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    # Apply security sanitization
    secure_logger(logger)
    
    return logger

def log_api_call(
    service: str,
    endpoint: str,
    status: str,
    response_time: Optional[float] = None,
    error_msg: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an API interaction with success/failure status.
    
    This function updates the in-memory metric registry and logs the event.
    
    Args:
        service: Name of the API service (e.g., 'npm', 'github', 'audit')
        endpoint: The API endpoint called
        status: 'success' or 'failure'
        response_time: Optional response time in seconds
        error_msg: Optional error message if status is failure
        payload: Optional request payload (will be sanitized)
    """
    logger = get_metric_logger()
    
    # Update registry
    _metric_registry["total"] += 1
    if status == "success":
        _metric_registry["success"] += 1
    else:
        _metric_registry["failure"] += 1
    
    # Sanitize sensitive data
    safe_service = sanitize_value(service)
    safe_endpoint = sanitize_value(endpoint)
    safe_error = sanitize_value(error_msg) if error_msg else None
    
    # Build log message
    message = f"API_CALL: service={safe_service}, endpoint={safe_endpoint}, status={status}"
    
    if response_time is not None:
        message += f", response_time={response_time:.3f}s"
    
    if safe_error:
        message += f", error={safe_error}"
    
    if payload:
        safe_payload = {k: sanitize_value(v) for k, v in payload.items()}
        message += f", payload={safe_payload}"
    
    if status == "success":
        logger.info(message)
    else:
        logger.error(message)

def get_metrics_snapshot() -> Dict[str, Any]:
    """
    Get the current snapshot of API metrics.
    
    Returns:
        Dictionary containing total, success, failure counts and calculated rates.
    """
    total = _metric_registry["total"]
    success = _metric_registry["success"]
    failure = _metric_registry["failure"]
    
    success_rate = (success / total * 100) if total > 0 else 0.0
    failure_rate = (failure / total * 100) if total > 0 else 0.0
    
    return {
        "total": total,
        "success": success,
        "failure": failure,
        "success_rate_percent": round(success_rate, 2),
        "failure_rate_percent": round(failure_rate, 2)
    }

def reset_metrics() -> None:
    """Reset the in-memory metric registry."""
    global _metric_registry
    _metric_registry = {
        "success": 0,
        "failure": 0,
        "total": 0
    }

# Initialize the root logger for the project
def init_project_logging() -> None:
    """
    Initialize the project-wide logging configuration.
    
    This should be called once at the start of the application.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, DEFAULT_LOG_LEVEL, logging.INFO))
    
    if not root_logger.handlers:
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        root_logger.addHandler(file_handler)
        
        secure_logger(root_logger)