import logging
import sys
import os
import re
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any

# Define custom exceptions for the project
class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass

class LLMRefactoringError(Exception):
    """Raised when LLM refactoring fails."""
    pass

class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass

class ModelInferenceError(Exception):
    """Raised when model inference fails."""
    pass

class ValidationFailedError(Exception):
    """Raised when validation fails."""
    pass

class CacheError(Exception):
    """Raised when cache operations fail."""
    pass

class SensitiveLogFilter(logging.Filter):
    """Filter to mask sensitive information like API keys in logs."""
    
    PATTERNS = [
        r"API_KEY=.*",
        r"HF_API_KEY=.*",
        r"token=.*",
        r"Authorization:.*"
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for pattern in self.PATTERNS:
            if re.search(pattern, msg, re.IGNORECASE):
                # Mask the sensitive part
                record.msg = re.sub(pattern, lambda m: m.group(0).split('=')[0] + '=***', msg, flags=re.IGNORECASE)
                record.args = () # Clear args to prevent formatting issues
        return True

def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure the root logger with a custom format and sensitive filter."""
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    
    # Add sensitive filter
    ch.addFilter(SensitiveLogFilter())
    
    logger.addHandler(ch)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Inherit level from root if not set
        if logger.level == logging.NOTSET:
            logger.setLevel(logging.INFO)
    return logger

@contextmanager
def timed_operation(operation_name: str):
    """Context manager to log execution time of an operation."""
    start_time = time.time()
    logger = get_logger(__name__)
    logger.info(f"Starting {operation_name}...")
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"Completed {operation_name} in {duration:.2f} seconds.")

def error_handler(error_class: Exception):
    """Decorator to handle specific errors and log them."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_class as e:
                logger = get_logger(__name__)
                logger.error(f"{error_class.__name__} occurred: {e}")
                raise
        return wrapper
    return decorator

def log_metric(metric_name: str, value: float, tags: Optional[Dict[str, Any]] = None):
    """Log a metric value."""
    logger = get_logger(__name__)
    msg = f"Metric: {metric_name} = {value}"
    if tags:
        tag_str = ", ".join([f"{k}={v}" for k, v in tags.items()])
        msg += f" | Tags: {tag_str}"
    logger.info(msg)
