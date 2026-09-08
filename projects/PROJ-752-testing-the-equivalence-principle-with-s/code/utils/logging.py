"""
Standardized logging and error handling utilities for the SLR Equivalence Principle pipeline.

This module provides:
- Custom exception hierarchy for specific failure modes
- Centralized logging configuration
- Progress tracking decorators and utilities
- Error handling wrappers
"""

import logging
import sys
import os
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import traceback
from functools import wraps

# Custom Exception Hierarchy
class PipelineError(Exception):
    """Base exception for all pipeline-related errors."""
    pass

class DataUnavailableError(PipelineError):
    """Raised when required data sources are missing or inaccessible."""
    pass

class ConfigurationError(PipelineError):
    """Raised when configuration validation fails."""
    pass

class AnalysisError(PipelineError):
    """Raised when an analysis step fails due to numerical or logical issues."""
    pass

class ModelConvergenceError(AnalysisError):
    """Raised when a model fitting algorithm fails to converge."""
    pass

class ValidationError(PipelineError):
    """Raised when data validation checks fail."""
    pass

# Logging Configuration
_logger_instance: Optional[logging.Logger] = None
_log_initialized = False

def init_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Initialize the global logger with standardized formatting.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to (in addition to console)
    
    Returns:
        Configured logger instance
    """
    global _logger_instance, _log_initialized
    
    if _log_initialized:
        return _logger_instance
    
    # Create logger
    logger = logging.getLogger("slr_pipeline")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Console handler with detailed format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Format: [TIMESTAMP] [LEVEL] [MODULE] MESSAGE
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Optional file handler
    if log_file:
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else ".", exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    _logger_instance = logger
    _log_initialized = True
    
    logger.info("Logging system initialized")
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance. If not initialized, creates one with defaults.
    
    Args:
        name: Sub-logger name (e.g., "slr_pipeline.data.ingestion")
    
    Returns:
        Logger instance
    """
    global _logger_instance
    if not _log_initialized:
        init_logging()
    
    if name:
        return logging.getLogger(f"slr_pipeline.{name}")
    return _logger_instance

def log_progress(step_name: str, current: int, total: int, message: Optional[str] = None) -> None:
    """
    Log a progress update for a multi-step process.
    
    Args:
        step_name: Name of the current step
        current: Current iteration count
        total: Total iterations
        message: Optional additional context message
    """
    logger = get_logger()
    percentage = (current / total) * 100 if total > 0 else 0
    status = f"Step '{step_name}': {current}/{total} ({percentage:.1f}%)"
    if message:
        status += f" - {message}"
    logger.info(status)

def log_error(error: Exception, context: Optional[str] = None, logger_name: Optional[str] = None) -> None:
    """
    Log an error with full traceback and optional context.
    
    Args:
        error: The exception to log
        context: Additional context about where the error occurred
        logger_name: Optional logger name override
    """
    logger = get_logger(logger_name)
    error_msg = f"{type(error).__name__}: {str(error)}"
    
    if context:
        logger.error(f"Context: {context} | {error_msg}")
    else:
        logger.error(error_msg)
    
    logger.debug("Traceback:\n" + traceback.format_exc())

def handle_fatal_error(error: Exception, exit_code: int = 1) -> None:
    """
    Log a fatal error and exit the process.
    
    Args:
        error: The fatal exception
        exit_code: Exit code to use
    """
    logger = get_logger()
    logger.critical(f"FATAL ERROR: {error}")
    logger.critical(traceback.format_exc())
    sys.exit(exit_code)

def log_step_duration(step_name: str, duration_seconds: float) -> None:
    """
    Log the duration of a completed step.
    
    Args:
        step_name: Name of the step
        duration_seconds: Time taken in seconds
    """
    logger = get_logger()
    if duration_seconds < 60:
        logger.info(f"Step '{step_name}' completed in {duration_seconds:.2f}s")
    else:
        minutes = duration_seconds / 60
        logger.info(f"Step '{step_name}' completed in {minutes:.2f}m ({duration_seconds:.2f}s)")

def track_step(step_name: str) -> Callable:
    """
    Decorator to track execution time and log progress for a function.
    
    Args:
        step_name: Name of the step for logging
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger(func.__module__)
            logger.info(f"Starting step: {step_name}")
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                log_step_duration(step_name, duration)
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                log_step_duration(step_name, duration)
                log_error(e, context=f"Failed during step: {step_name}", logger_name=func.__module__)
                raise
        return wrapper
    return decorator

# Context Manager for timed steps
class TimedStep:
    """Context manager for timing and logging code blocks."""
    
    def __init__(self, step_name: str, logger_name: Optional[str] = None):
        self.step_name = step_name
        self.logger_name = logger_name
        self.start_time: Optional[datetime] = None
        self.logger: Optional[logging.Logger] = None
    
    def __enter__(self):
        self.logger = get_logger(self.logger_name)
        self.logger.info(f"Entering step: {self.step_name}")
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type is None:
            log_step_duration(self.step_name, duration)
        else:
            log_error(exc_val, context=f"Step '{self.step_name}' failed", logger_name=self.logger_name)
            log_step_duration(self.step_name, duration)
        return False  # Do not suppress exceptions