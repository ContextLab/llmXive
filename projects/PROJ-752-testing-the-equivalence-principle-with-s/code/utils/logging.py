"""
Standardized logging utilities for the Equivalence Principle Pipeline.

Provides consistent error handling, progress logging, and structured output.
"""
import logging
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime
import traceback

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataUnavailableError(PipelineError):
    """Raised when required data is missing or unavailable."""
    pass

class ConfigurationError(PipelineError):
    """Raised when configuration is invalid."""
    pass

class AnalysisError(PipelineError):
    """Raised when an analysis step fails."""
    pass

_logger_instance: Optional[logging.Logger] = None
_logging_initialized: bool = False

def init_logging(level: str = "INFO") -> None:
    """
    Initialize the root logger with standard formatting.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
    """
    global _logger_instance, _logging_initialized
    
    if _logging_initialized:
        return
        
    _logger_instance = logging.getLogger("llmXive_pipeline")
    _logger_instance.setLevel(getattr(logging, level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    _logger_instance.addHandler(console_handler)
    _logging_initialized = True

def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger for a specific module.
    
    Args:
        name: Module name (e.g., __name__).
        
    Returns:
        Configured logger instance.
    """
    if not _logging_initialized:
        init_logging()
    return logging.getLogger(f"llmXive_pipeline.{name}")

def log_progress(logger: logging.Logger, message: str) -> None:
    """
    Log a progress message at INFO level.
    
    Args:
        logger: Logger instance.
        message: Progress message.
    """
    logger.info(f"[PROGRESS] {message}")

def log_error(logger: logging.Logger, message: str) -> None:
    """
    Log an error message at ERROR level.
    
    Args:
        logger: Logger instance.
        message: Error message.
    """
    logger.error(f"[ERROR] {message}")

def handle_fatal_error(logger: logging.Logger, exception: Exception, context: str) -> None:
    """
    Log a fatal error with full traceback and exit.
    
    Args:
        logger: Logger instance.
        exception: The exception that occurred.
        context: Contextual description of where it failed.
    """
    logger.critical(f"[FATAL] {context}: {str(exception)}")
    logger.critical(traceback.format_exc())
    raise SystemExit(1)
