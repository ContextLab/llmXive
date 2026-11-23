"""
Structured logging utility module for the Photo-Fries rearrangement study.

Provides centralized logging configuration and operation logging for
reproducibility and audit trail purposes.
"""

import logging
import sys
from typing import Any, Dict, Optional


def setup_logging(level: str = "INFO") -> None:
    """
    Configure structured logging for the project.
    
    Args:
        level: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    root_logger.addHandler(handler)


def log_operation(operation: str, **kwargs) -> None:
    """
    Log a structured operation with metadata.
    
    Args:
        operation: Name of the operation being logged.
        **kwargs: Additional metadata to include in the log.
    """
    logger = logging.getLogger(__name__)
    
    # Build message with metadata
    metadata_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    if metadata_str:
        logger.info(f"OPERATION[{operation}]: {metadata_str}")
    else:
        logger.info(f"OPERATION[{operation}]")


def log_environmental_params(**kwargs) -> None:
    """
    Log environmental parameters for a run.
    
    Args:
        **kwargs: Environmental parameters (temperature, humidity, etc.).
    """
    logger = logging.getLogger(__name__)
    
    params_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"ENVIRONMENT: {params_str}")