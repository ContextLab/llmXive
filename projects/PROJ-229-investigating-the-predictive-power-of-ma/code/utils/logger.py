import logging
import sys
import os
import traceback
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from config import get_config

_logger: Optional[logging.Logger] = None
_handler: Optional[logging.Handler] = None

def setup_logger(
    name: str = "llmXive",
    level: Optional[int] = None,
    log_file: Optional[str] = None,
    use_color: bool = True
) -> logging.Logger:
    """
    Configure the global logger instance for the pipeline.
    
    Args:
        name: Logger name.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If provided, logs are written there.
        use_color: Whether to use ANSI color codes in console output.
    
    Returns:
        The configured logger instance.
    """
    global _logger, _handler
    
    if _logger is not None:
        return _logger

    config = get_config()
    if level is None:
        # Default to INFO unless DEBUG is explicitly set in config
        level_str = config.get("logging", {}).get("level", "INFO")
        level = getattr(logging, level_str.upper(), logging.INFO)

    _logger = logging.getLogger(name)
    _logger.setLevel(level)
    
    # Prevent adding multiple handlers if called multiple times
    if _logger.handlers:
        return _logger

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Simple formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    # File Handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)

    return _logger

def get_pipeline_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieve the initialized pipeline logger.
    If not initialized, initializes it with default settings from config.
    
    Args:
        name: Logger name (default 'llmXive').
    
    Returns:
        The logger instance.
    """
    global _logger
    if _logger is None:
        # Initialize with defaults if not explicitly set up yet
        _logger = setup_logger(name)
    return _logger

def log_error(error: Exception, context: str = "Pipeline Error") -> None:
    """
    Log an exception with context using the pipeline logger.
    
    Args:
        error: The exception to log.
        context: A string describing the context where the error occurred.
    """
    logger = get_pipeline_logger()
    logger.error(f"{context}: {error.__class__.__name__} - {str(error)}")
    tb_str = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    logger.debug(f"Traceback: {tb_str}")

def log_warning(message: str) -> None:
    """
    Log a warning message.
    
    Args:
        message: The warning message.
    """
    logger = get_pipeline_logger()
    logger.warning(message)

def log_info(message: str) -> None:
    """
    Log an info message.
    
    Args:
        message: The info message.
    """
    logger = get_pipeline_logger()
    logger.info(message)

def log_debug(message: str) -> None:
    """
    Log a debug message.
    
    Args:
        message: The debug message.
    """
    logger = get_pipeline_logger()
    logger.debug(message)

def log_critical(message: str) -> None:
    """
    Log a critical message.
    
    Args:
        message: The critical message.
    """
    logger = get_pipeline_logger()
    logger.critical(message)

def log_exception_details(error: Exception, context: str = "Unhandled Exception") -> None:
    """
    Log detailed exception information including traceback.
    
    Args:
        error: The exception instance.
        context: Contextual description of where the error occurred.
    """
    logger = get_pipeline_logger()
    logger.critical(f"{context}: {error.__class__.__name__} - {str(error)}")
    logger.critical(f"Traceback:\n{''.join(traceback.format_exception(type(error), error, error.__traceback__))}")
    
    # Attempt to log additional context if available
    if hasattr(error, 'context'):
        logger.critical(f"Error Context: {error.context}")

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

class DataFetchError(PipelineError):
    """Exception raised when data fetching fails."""
    pass

class DataProcessingError(PipelineError):
    """Exception raised when data processing fails."""
    pass

class ModelTrainingError(PipelineError):
    """Exception raised when model training fails."""
    pass

class ConfigError(PipelineError):
    """Exception raised when configuration is invalid."""
    pass

def handle_error(error: Exception, context: str = "Pipeline Error", reraise: bool = True) -> None:
    """
    Centralized error handling function.
    
    Args:
        error: The exception to handle.
        context: Contextual description of the error.
        reraise: If True, re-raises the exception after logging.
    """
    logger = get_pipeline_logger()
    log_error(error, context)
    
    if reraise:
        raise error

def validate_not_null(value: Any, field_name: str) -> Any:
    """
    Validate that a value is not None.
    
    Args:
        value: The value to validate.
        field_name: Name of the field for error messaging.
    
    Returns:
        The value if valid.
    
    Raises:
        ValueError: If the value is None.
    """
    if value is None:
        raise ValueError(f"{field_name} cannot be None")
    return value

def validate_positive(value: float, field_name: str) -> float:
    """
    Validate that a numeric value is positive.
    
    Args:
        value: The value to validate.
        field_name: Name of the field for error messaging.
    
    Returns:
        The value if valid.
    
    Raises:
        ValueError: If the value is not positive.
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value
