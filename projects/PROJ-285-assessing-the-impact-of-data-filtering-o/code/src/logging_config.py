"""
Logging and Error Handling Infrastructure for PROJ-285.

This module provides centralized logging configuration and custom exception
classes used across the pipeline to ensure consistent error reporting,
debugging capabilities, and audit trails.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional

# Custom Exception Hierarchy
class PipelineError(Exception):
    """Base exception for all pipeline-specific errors."""
    def __init__(self, message: str, context: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

class DataIngestionError(PipelineError):
    """Raised when data loading or parsing fails."""
    pass

class ThresholdFilterError(PipelineError):
    """Raised when threshold filtering logic encounters invalid data."""
    pass

class CoordinateMatchError(PipelineError):
    """Raised when coordinate matching fails due to invalid inputs."""
    pass

class StatisticalAnalysisError(PipelineError):
    """Raised when statistical calculations fail."""
    pass

class ConfigError(PipelineError):
    """Raised when configuration or environment setup is invalid."""
    pass

# Logging Configuration
_logger_initialized = False
_log_file_path: Optional[Path] = None

def get_log_file_path() -> Path:
    """Returns the path to the current log file."""
    if _log_file_path is None:
        raise ConfigError("Logging not initialized. Call configure_logging first.")
    return _log_file_path

def configure_logging(log_level: str = "INFO", log_dir: str = "data/processed", console: bool = True) -> None:
    """
    Configures the root logger for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_dir: Directory to store log files. Defaults to 'data/processed'.
        console: If True, also logs to stdout/stderr.
    """
    global _logger_initialized, _log_file_path

    if _logger_initialized:
        return

    # Ensure log directory exists
    log_path_obj = Path(log_dir)
    log_path_obj.mkdir(parents=True, exist_ok=True)

    # Create unique log filename with timestamp
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"pipeline_{timestamp}.log"
    _log_file_path = log_path_obj / log_filename

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers = []

    # File Handler
    try:
        file_handler = logging.FileHandler(_log_file_path)
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}", file=sys.stderr)

    # Console Handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        console_format = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
        console_handler.setFormatter(console_format)
        root_logger.addHandler(console_handler)

    _logger_initialized = True
    logging.info("Logging infrastructure initialized successfully.")

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves or creates a logger with the specified name.

    Args:
        name: Logger name (usually __name__ of the module).

    Returns:
        Configured Logger instance.
    """
    if not _logger_initialized:
        configure_logging()
    return logging.getLogger(name)

def log_exception(e: Exception, level: str = "ERROR", msg: Optional[str] = None) -> None:
    """
    Logs an exception with full traceback context.

    Args:
        e: The exception instance.
        level: Log level (INFO, WARNING, ERROR, CRITICAL).
        msg: Optional custom message prefix.
    """
    logger = get_logger(__name__)
    log_func = getattr(logger, level.lower(), logger.error)
    
    full_msg = f"Exception occurred: {msg or str(e)}"
    import traceback
    tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
    
    log_func(f"{full_msg}\n{tb_str}")
    
    # If it's a custom PipelineError, re-raise or handle specifically if needed
    if isinstance(e, PipelineError) and not isinstance(e, ConfigError):
        # Optional: Re-raise to let the caller handle it if it's not just logging
        pass

# Context Manager for safe execution blocks
class SafeExecutionBlock:
    """
    Context manager to wrap code blocks with automatic error logging and handling.
    
    Usage:
        with SafeExecutionBlock("Data Loading Phase"):
            load_data()
    """
    def __init__(self, phase_name: str, raise_on_error: bool = True):
        self.phase_name = phase_name
        self.raise_on_error = raise_on_error
        self.logger = get_logger(__name__)

    def __enter__(self):
        self.logger.info(f"Starting phase: {self.phase_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(f"Phase '{self.phase_name}' failed: {str(exc_val)}")
            if self.raise_on_error:
                # Re-raise to stop execution unless handled
                return False
        else:
            self.logger.info(f"Phase '{self.phase_name}' completed successfully.")
        return False  # Always return False to propagate exceptions if they occurred
