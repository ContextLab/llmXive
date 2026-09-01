"""
Logging Utilities.

Provides structured logging for environmental parameters and compliance checks.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class EnvironmentalFormatter(logging.Formatter):
    """Custom formatter for environmental logs."""
    
    def format(self, record):
        # Add timestamp and level
        base_msg = super().format(record)
        
        # If the record has environmental data, format it nicely
        if hasattr(record, 'env_data'):
            env_str = json.dumps(record.env_data, indent=2)
            return f"{base_msg}\n{env_str}"
        
        return base_msg


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for log output
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = EnvironmentalFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = EnvironmentalFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_environmental_params(
    logger: logging.Logger,
    params: Dict[str, Any],
    level: int = logging.INFO
) -> None:
    """
    Log environmental parameters as a structured record.
    
    Args:
        logger: Logger instance
        params: Dictionary of parameters
        level: Logging level
    """
    logger.log(level, "Environmental Parameters", extra={'env_data': params})


def log_compliance_check(
    logger: logging.Logger,
    check_name: str,
    passed: bool,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a compliance check result.
    
    Args:
        logger: Logger instance
        check_name: Name of the compliance check
        passed: Whether the check passed
        details: Optional details about the check
    """
    status = "PASSED" if passed else "FAILED"
    msg = f"Compliance Check: {check_name} - {status}"
    
    if details:
        logger.info(msg, extra={'env_data': details})
    else:
        logger.info(msg)
