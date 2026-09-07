"""
Standardized logging and error handling utilities for the llmXive SLR pipeline.

Provides:
- Custom exception hierarchy for domain-specific errors.
- Configured logging handlers (file + console).
- Progress tracking and error logging helpers.
"""
import logging
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime
import traceback

# --- Custom Exception Hierarchy ---

class PipelineError(Exception):
    """Base exception for all pipeline-related errors."""
    pass

class DataUnavailableError(PipelineError):
    """Raised when required data is missing or inaccessible."""
    pass

class ConfigurationError(PipelineError):
    """Raised when configuration loading or validation fails."""
    pass

class AnalysisError(PipelineError):
    """Raised when an analysis step fails (e.g., non-convergence)."""
    pass

# --- Logging Configuration ---

_logger_instance: Optional[logging.Logger] = None
_log_initialized = False

def init_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Initialize the root logger for the project.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file. If None, only console output is used.
        
    Returns:
        The configured logger instance.
    """
    global _logger_instance, _log_initialized
    
    if _log_initialized:
        return _logger_instance  # type: ignore

    _logger_instance = logging.getLogger("slr_pipeline")
    _logger_instance.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers to avoid duplicates in interactive environments
    _logger_instance.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    _logger_instance.addHandler(console_handler)

    # File Handler (if specified)
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        _logger_instance.addHandler(file_handler)

    _log_initialized = True
    return _logger_instance

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, initializing it if necessary.
    
    Args:
        name: Sub-logger name (e.g., 'data.ingestion'). If None, returns the root logger.
        
    Returns:
        Configured logger instance.
    """
    if not _log_initialized:
        init_logging()
    
    if name:
        return logging.getLogger(f"slr_pipeline.{name}")
    return _logger_instance  # type: ignore

def log_progress(stage: str, current: int, total: int, message: str = "") -> None:
    """
    Log a progress update for a multi-step process.
    
    Args:
        stage: Name of the current stage (e.g., 'Fetching Satellites').
        current: Current step number (1-indexed).
        total: Total number of steps.
        message: Optional additional context message.
    """
    logger = get_logger()
    percent = (current / total) * 100
    status = f"Progress: {stage} ({current}/{total}) - {percent:.1f}%"
    if message:
        status += f" | {message}"
    logger.info(status)

def log_error(error: Exception, context: str = "", level: str = "ERROR") -> None:
    """
    Log an error with stack trace and optional context.
    
    Args:
        error: The exception instance.
        context: Optional string describing what was happening when the error occurred.
        level: Logging level string ('ERROR', 'CRITICAL').
    """
    logger = get_logger()
    log_method = getattr(logger, level.lower(), logger.error)
    
    msg = f"Error in {context}: {str(error)}" if context else f"Error: {str(error)}"
    log_method(msg)
    log_method("Traceback:\n%s", traceback.format_exc())

def handle_fatal_error(error: Exception, context: str = "") -> None:
    """
    Log a fatal error and exit the program.
    
    Args:
        error: The exception instance.
        context: Optional context string.
    """
    log_error(error, context, level="CRITICAL")
    sys.exit(1)