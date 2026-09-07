"""
Deterministic logging and error handling infrastructure.

Provides setup_logger() for consistent logging configuration and
log_error() for structured error logging and raising.
"""
import logging
import sys
import traceback
from pathlib import Path
from typing import Optional
from datetime import datetime

# Import config for consistent settings
try:
    from config import get_log_level, get_output_dir
except ImportError:
    # Fallback if running from code/ directly
    from config import get_log_level, get_output_dir


# Custom exception hierarchy for structured error handling
class ResearchError(Exception):
    """Base class for research pipeline errors."""
    def __init__(self, message: str, context: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat()


class DataLoadError(ResearchError):
    """Error during data loading or preprocessing."""
    pass


class ModelExecutionError(ResearchError):
    """Error during model inference or execution."""
    pass


class ConfigurationError(ResearchError):
    """Error in configuration or validation."""
    pass


class AnalysisError(ResearchError):
    """Error during analysis or computation."""
    pass


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Set up a deterministic logger with consistent formatting.
    
    Args:
        name: Logger name (typically __name__)
        log_file: Optional path to log file (relative to get_output_dir())
        level: Log level as string (e.g., "INFO", "DEBUG"). If None, uses get_log_level().
        console: Whether to log to console (stderr)
        
    Returns:
        Configured logger instance
        
    Example:
        logger = setup_logger(__name__, "experiments/run.log", "INFO")
        logger.info("Starting experiment")
    """
    # Get logger
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()
    
    # Set level
    log_level = level or get_log_level()
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatter with deterministic format
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if log_file specified
    if log_file:
        output_dir = Path(get_output_dir())
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / log_file
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(str(file_path), mode='a')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_error(
    logger: logging.Logger,
    error: Exception,
    message: Optional[str] = None,
    context: Optional[dict] = None,
    should_raise: bool = True
) -> None:
    """
    Log an error with full traceback and optional context, then optionally re-raise.
    
    This function ensures consistent error logging across the pipeline and
    provides structured error context for debugging.
    
    Args:
        logger: Logger instance to use
        error: The exception instance to log
        message: Optional custom message to prepend to the error
        context: Optional dictionary of contextual information (e.g., instance_id, strategy)
        should_raise: If True, re-raise the exception after logging
        
    Raises:
        The original exception if should_raise is True
        
    Example:
        try:
            result = risky_operation()
        except Exception as e:
            log_error(logger, e, "Failed to process instance", 
                     {"instance_id": 42, "strategy": "tfidf"})
            # Exception is re-raised by default
    """
    # Build context string
    context_str = ""
    if context:
        context_items = ", ".join(f"{k}={v}" for k, v in context.items())
        context_str = f" | Context: {{{context_items}}}"
    
    # Build log message
    if message:
        log_msg = f"{message}: {str(error)}{context_str}"
    else:
        log_msg = f"{type(error).__name__}: {str(error)}{context_str}"
    
    # Log at ERROR level
    logger.error(log_msg, exc_info=False)
    
    # Log full traceback at DEBUG level for detailed debugging
    logger.debug(
        f"Full traceback for {type(error).__name__}:\n" + 
        traceback.format_exc()
    )
    
    # Log to the ResearchError context if it's a custom error
    if isinstance(error, ResearchError) and error.context:
        logger.debug(f"Error context: {error.context}")
    
    # Re-raise if requested
    if should_raise:
        raise error


def safe_execute(func, logger: Optional[logging.Logger] = None, *args, **kwargs):
    """
    Execute a function with automatic error logging and structured exceptions.
    
    Args:
        func: Function to execute
        logger: Optional logger instance (creates default if None)
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func if successful
        
    Raises:
        ResearchError (or subclass) if execution fails, with full context
    """
    if logger is None:
        logger = setup_logger(__name__)
    
    try:
        return func(*args, **kwargs)
    except ResearchError:
        # Re-raise ResearchErrors with context preserved
        raise
    except Exception as e:
        # Wrap unexpected errors
        error = ResearchError(
            message=f"Unexpected error in {func.__name__}",
            context={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)}
        )
        log_error(logger, error, should_raise=True)
        
