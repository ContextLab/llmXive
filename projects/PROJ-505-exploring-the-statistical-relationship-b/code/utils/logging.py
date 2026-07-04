"""
Logging and error handling infrastructure for the solar wind composition analysis pipeline.

Provides centralized logging configuration, custom exceptions, and error handling utilities.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Custom Exception Hierarchy
class PipelineError(Exception):
    """Base exception for all pipeline-related errors."""
    pass

class DataIngestionError(PipelineError):
    """Raised when data ingestion (download or parsing) fails."""
    pass

class AlignmentError(PipelineError):
    """Raised when temporal alignment or resampling fails."""
    pass

class AnalysisError(PipelineError):
    """Raised during statistical analysis or model fitting."""
    pass

class ConfigError(PipelineError):
    """Raised when configuration is missing or invalid."""
    pass

class ValidationError(PipelineError):
    """Raised when data validation checks fail."""
    pass

# Logger Configuration
_logger: Optional[logging.Logger] = None
_initialized: bool = False

def get_logger(name: str = "solar_wind_pipeline") -> logging.Logger:
    """
    Returns the configured logger instance.
    Initializes logging if not already done.
    """
    global _logger, _initialized
    
    if not _initialized:
        setup_logging()
    
    if _logger is None:
        _logger = logging.getLogger(name)
    
    return _logger

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None
) -> None:
    """
    Configure the root logger with console and optional file handlers.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Path to log file. If None, only console output is used.
        project_root: Base directory for the project. Defaults to current working directory.
    """
    global _logger, _initialized
    
    if _initialized:
        return

    # Determine project root if not provided
    if project_root is None:
        project_root = Path.cwd()
    
    # Create log directory if file logging is requested
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Default log file path
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = str(log_dir / f"pipeline_{timestamp}.log")
    else:
        # Ensure the path is relative to project_root if it's a string
        log_file = str(project_root / log_file)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File Handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)
    
    _logger = logging.getLogger("solar_wind_pipeline")
    _initialized = True
    
    _logger.info(f"Logging initialized. Log file: {log_file}")

def log_error_and_raise(error: Exception, context: Optional[str] = None, raise_exception: bool = True) -> None:
    """
    Logs an error with context and optionally re-raises it.
    
    Args:
        error: The exception instance to log.
        context: Additional context string to include in the log.
        raise_exception: If True, re-raises the exception after logging.
    """
    logger = get_logger()
    msg = str(error)
    if context:
        msg = f"{context}: {msg}"
    
    logger.error(msg, exc_info=True)
    
    if raise_exception:
        raise error

def safe_execute(func, *args, default=None, on_error: Optional[str] = None) -> Any:
    """
    Executes a function and returns a default value on error, optionally logging the error.
    
    Args:
        func: The function to execute.
        *args: Arguments to pass to the function.
        default: Value to return if an exception occurs.
        on_error: Optional message to log if an error occurs.
        
    Returns:
        The result of func(*args) or the default value.
    """
    logger = get_logger()
    try:
        return func(*args)
    except Exception as e:
        if on_error:
            logger.warning(f"{on_error}: {e}")
        else:
            logger.debug(f"Safe execution failed: {e}")
        return default

# Context manager for timing operations
from contextlib import contextmanager

@contextmanager
def log_duration(name: str, logger_name: Optional[str] = None):
    """
    Context manager to log the duration of a block of code.
    
    Args:
        name: Name of the operation being timed.
        logger_name: Optional specific logger name. Defaults to "solar_wind_pipeline".
    """
    logger = get_logger(logger_name) if logger_name else get_logger()
    start_time = datetime.now()
    logger.debug(f"Starting {name}...")
    try:
        yield
    finally:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Completed {name} in {duration:.2f} seconds.")

def check_memory_usage(threshold_gb: float = 6.0) -> bool:
    """
    Checks current memory usage against a threshold.
    
    Args:
        threshold_gb: Threshold in Gigabytes.
        
    Returns:
        True if usage is below threshold, False otherwise.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 * 1024)
        mem_gb = mem_mb / 1024
        
        if mem_gb > threshold_gb:
            logger = get_logger()
            logger.warning(f"Memory usage ({mem_gb:.2f} GB) exceeds threshold ({threshold_gb} GB).")
            return False
        return True
    except ImportError:
        # psutil not installed, skip check
        return True
    except Exception as e:
        logger = get_logger()
        logger.warning(f"Could not check memory usage: {e}")
        return True

# Initialize logging at module load if needed, or wait for explicit call
# setup_logging() is called by get_logger() on first access to ensure config is set.