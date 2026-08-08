"""
Robust logging and error handling infrastructure for the LLM Refactoring pipeline.

This module provides:
- A centralized logger configuration with console and file handlers.
- Log masking for sensitive information (API keys).
- Custom exception hierarchy for domain-specific errors.
- Context managers for timed operations and error handling.
"""

import logging
import sys
import os
import re
import time
from contextlib import contextmanager
from typing import Optional, Generator, Any, Callable
from functools import wraps

# Import config to get paths/secrets if needed, though logging setup is mostly independent
# We assume code/config.py exists as per completed tasks T004/T002
try:
    from config import get_secret
except ImportError:
    # Fallback if config is not yet importable during early boot, though unlikely in this order
    get_secret = None


# --- Constants ---
LOG_DIR = "logs"
LOG_FILE_NAME = "pipeline.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Regex patterns for sensitive data masking
# Matches HF API key format (usually starts with 'hf_')
HF_KEY_PATTERN = re.compile(r'(hf_[a-zA-Z0-9]{34})')
# Generic Bearer token
BEARER_PATTERN = re.compile(r'(Bearer\s+[a-zA-Z0-9_-]+)')


# --- Custom Exceptions ---
class LLMRefactoringError(Exception):
    """Base exception for all LLM Refactoring pipeline errors."""
    pass


class ConfigError(LLMRefactoringError):
    """Raised when configuration is invalid or missing."""
    pass


class DataFetchError(LLMRefactoringError):
    """Raised when fetching external data (e.g., BigCode) fails."""
    pass


class ModelInferenceError(LLMRefactoringError):
    """Raised when LLM API calls fail or return invalid responses."""
    pass


class ValidationFailedError(LLMRefactoringError):
    """Raised when data validation (Pydantic/Schema) fails."""
    pass


class CacheError(LLMRefactoringError):
    """Raised when cache operations fail."""
    pass


# --- Logging Setup ---

def _mask_sensitive_info(message: str) -> str:
    """Mask sensitive information in log messages."""
    if not message:
        return message
    
    masked = HF_KEY_PATTERN.sub("[REDACTED_HF_KEY]", message)
    masked = BEARER_PATTERN.sub("Bearer [REDACTED_TOKEN]", masked)
    
    # Fallback: if get_secret is available, try to mask the actual key value
    if get_secret:
        try:
            key = get_secret("HF_API_KEY")
            if key and len(key) > 4:
                masked = masked.replace(key, "[REDACTED_HF_KEY]")
        except Exception:
            pass # Ignore errors during masking to prevent logging failures
    
    return masked


class SensitiveLogFilter(logging.Filter):
    """Logging filter that masks sensitive data in records."""
    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = _mask_sensitive_info(record.msg)
        if hasattr(record, 'args') and record.args:
            # Handle formatted args if any
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    new_args.append(_mask_sensitive_info(arg))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)
        return True


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_dir: Optional[str] = None
) -> logging.Logger:
    """
    Configure the root logger and return a named logger for the project.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_to_file: Whether to write logs to a file.
        log_dir: Directory for log files. Defaults to 'logs' relative to project root.

    Returns:
        A configured logger instance named 'llm_refactor'.
    """
    logger = logging.getLogger("llm_refactor")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveLogFilter())
    logger.addHandler(console_handler)

    # File Handler
    if log_to_file:
        directory = log_dir or LOG_DIR
        os.makedirs(directory, exist_ok=True)
        log_path = os.path.join(directory, LOG_FILE_NAME)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(SensitiveLogFilter())
        logger.addHandler(file_handler)

    # Set root logger to avoid duplicate propagation if needed, 
    # but usually we want to capture everything in our specific logger
    logger.propagate = False

    return logger


# Global logger instance, initialized on first use
_logger: Optional[logging.Logger] = None

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get the project logger. Initializes it if not already done.
    
    Args:
        name: Optional sub-logger name (e.g., 'llm_refactor.download').
    
    Returns:
        A logger instance.
    """
    global _logger
    if _logger is None:
        _logger = setup_logging()
    
    if name:
        return _logger.getChild(name)
    return _logger


# --- Context Managers & Decorators ---

@contextmanager
def timed_operation(operation_name: str, logger: Optional[logging.Logger] = None) -> Generator[None, None, None]:
    """
    Context manager to log the duration of an operation.
    
    Usage:
        with timed_operation("Downloading dataset"):
            download_data()
    """
    start_time = time.time()
    log = logger or get_logger()
    log.info(f"Starting operation: {operation_name}")
    try:
        yield
        duration = time.time() - start_time
        log.info(f"Completed operation: {operation_name} in {duration:.2f}s")
    except Exception as e:
        duration = time.time() - start_time
        log.error(f"Operation failed: {operation_name} after {duration:.2f}s. Error: {e}")
        raise

@contextmanager
def error_handler(
    operation_name: str,
    logger: Optional[logging.Logger] = None,
    reraise: bool = True,
    exception_map: Optional[dict] = None
) -> Generator[None, None, None]:
    """
    Context manager to catch, log, and optionally re-raise or transform exceptions.
    
    Args:
        operation_name: Name of the operation for logging.
        logger: Logger instance.
        reraise: If True, re-raise the exception after logging.
        exception_map: Dict mapping specific exception types to custom LLMRefactoringError types.
    """
    log = logger or get_logger()
    try:
        yield
    except Exception as e:
        log.error(f"Error in operation '{operation_name}': {e}", exc_info=True)
        
        if exception_map:
            for exc_type, mapped_type in exception_map.items():
                if isinstance(e, exc_type):
                    raise mapped_type(f"Failed in {operation_name}: {e}") from e
        
        if reraise:
            raise

def handle_errors(operation_name: str, exception_map: Optional[dict] = None):
    """
    Decorator to wrap a function with error handling and logging.
    
    Args:
        operation_name: Name of the operation.
        exception_map: Optional mapping of exceptions to custom errors.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with error_handler(operation_name, exception_map=exception_map):
                return func(*args, **kwargs)
        return wrapper
    return decorator