"""
Base logging configuration and error handling utilities for the llmXive pipeline.

Provides a centralized logging setup that formats messages consistently across
all modules and handles uncaught exceptions gracefully.
"""
import logging
import sys
import traceback
from pathlib import Path
from typing import Optional, Dict, Any

# Default log level for the pipeline
DEFAULT_LOG_LEVEL = logging.INFO

# Formatter for console output
CONSOLE_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Formatter for file output (includes filename/line number for debugging)
FILE_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

_logger_registry: Dict[str, logging.Logger] = {}

def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[Path] = None,
    project_root: Optional[Path] = None
) -> logging.Logger:
    """
    Configure the root logger for the llmXive pipeline.
    
    Args:
        log_level: The minimum severity level to log (e.g., logging.INFO).
        log_file: Optional path to a log file. If provided, logs are also written to disk.
        project_root: Optional base path for relative log file resolution.
        
    Returns:
        The configured root logger instance.
        
    Raises:
        ValueError: If log_level is invalid.
    """
    if not isinstance(log_level, int) or log_level not in logging._levelToName:
        raise ValueError(f"Invalid log level: {log_level}")

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates on re-initialization
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(CONSOLE_FORMATTER)
    root_logger.addHandler(console_handler)

    # File Handler (optional)
    if log_file:
        # Resolve relative to project_root if provided
        if project_root and not log_file.is_absolute():
            log_file = project_root / log_file
        
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(FILE_FORMATTER)
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party logs if necessary (e.g., datasets, urllib3)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("datasets").setLevel(logging.WARNING)
    logging.getLogger("fsspec").setLevel(logging.WARNING)

    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a logger instance by name.
    
    Creates the logger if it doesn't exist and registers it.
    
    Args:
        name: The name of the logger (usually __name__ of the module).
        
    Returns:
        A configured logger instance.
    """
    if name not in _logger_registry:
        logger = logging.getLogger(name)
        if not logger.handlers:
            # Inherits level and handlers from root logger
            pass 
        _logger_registry[name] = logger
    return _logger_registry[name]

def handle_exception(
    logger: Optional[logging.Logger] = None,
    message: str = "An unexpected error occurred",
    exit_on_error: bool = False
) -> None:
    """
    Handle an uncaught exception by logging the full traceback and optionally exiting.
    
    This utility is intended to be used in `except Exception:` blocks to ensure
    consistent error reporting across the pipeline.
    
    Args:
        logger: The logger to use. If None, uses the root logger.
        message: A human-readable description of the error context.
        exit_on_error: If True, calls sys.exit(1) after logging.
        
    Raises:
        SystemExit: If exit_on_error is True.
    """
    if logger is None:
        logger = logging.getLogger()
    
    exc_type, exc_value, exc_tb = sys.exc_info()
    
    if exc_type is not None:
        full_traceback = traceback.format_exception(exc_type, exc_value, exc_tb)
        formatted_traceback = "".join(full_traceback)
        
        logger.error(f"{message}: {exc_value}")
        logger.debug("Traceback:\n%s", formatted_traceback)
        
        if exit_on_error:
            sys.exit(1)
    else:
        logger.error(f"{message}: No active exception to log.")
        if exit_on_error:
            sys.exit(1)

class PipelineError(Exception):
    """Base exception for all llmXive pipeline errors."""
    pass

class DataFetchError(PipelineError):
    """Raised when a data source is unreachable or invalid."""
    pass

class ValidationError(PipelineError):
    """Raised when data or model output fails schema validation."""
    pass

class ConfigurationError(PipelineError):
    """Raised when configuration files are missing or malformed."""
    pass