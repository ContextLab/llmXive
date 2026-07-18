"""
Core utilities for the llmXive pipeline.
Provides logging, error handling, and configuration helpers.
"""
import logging
import sys
import os
import traceback
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

# Custom Exceptions
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataUnavailableError(PipelineError):
    """Raised when required data is missing or fetchable."""
    pass

class InsufficientDataError(PipelineError):
    """Raised when data volume is below minimum requirements (e.g., <10 subjects)."""
    pass

class ConfigError(PipelineError):
    """Raised when configuration is invalid or missing required keys."""
    pass

class IntegrityError(PipelineError):
    """Raised when data integrity checks fail (e.g., hash mismatch)."""
    pass

# Logging Setup
_logger_instance: Optional[logging.Logger] = None

def setup_logging(
    name: str = "llmXive",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return the project logger.
    
    Args:
        name: Logger name.
        level: Logging level.
        log_file: Optional path to log file.
    
    Returns:
        Configured logger instance.
    """
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    _logger_instance = logger
    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get an existing logger or create a new one if not configured.
    
    Args:
        name: Logger name.
    
    Returns:
        Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Fallback to basic config if setup_logging wasn't called
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    return logger

def log_exception(
    logger: logging.Logger,
    exc: Exception,
    msg: Optional[str] = None
) -> None:
    """
    Log an exception with full traceback.
    
    Args:
        logger: Logger instance.
        exc: Exception object.
        msg: Optional custom message prefix.
    """
    error_msg = f"{msg}: {str(exc)}" if msg else str(exc)
    logger.error(error_msg)
    logger.debug(traceback.format_exc())
