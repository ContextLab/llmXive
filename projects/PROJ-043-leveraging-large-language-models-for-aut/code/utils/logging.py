"""
Logging and error handling infrastructure.
"""
import logging
import sys
import os
import re
import time
from contextlib import contextmanager
from typing import Optional

class LLMRefactoringError(Exception):
    """Base exception for the refactoring pipeline."""
    pass

class ConfigError(LLMRefactoringError):
    """Configuration validation error."""
    pass

class DataFetchError(LLMRefactoringError):
    """Error fetching data from external sources."""
    pass

class ModelInferenceError(LLMRefactoringError):
    """Error during model inference."""
    pass

class ValidationFailedError(LLMRefactoringError):
    """Data validation failed."""
    pass

class CacheError(LLMRefactoringError):
    """Cache operation failed."""
    pass

class SensitiveLogFilter(logging.Filter):
    """Filter to mask sensitive information in logs."""
    
    SENSITIVE_PATTERNS = [
        r'HF_API_KEY=\S+',
        r'Authorization: Bearer \S+',
        r'api_key=\S+'
    ]

    def filter(self, record):
        msg = record.getMessage()
        for pattern in self.SENSITIVE_PATTERNS:
            msg = re.sub(pattern, r'\g<0> [MASKED]', msg)
        return True

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return the root logger.
    
    Args:
        level: Logging level.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.addFilter(SensitiveLogFilter())
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a named logger with project-specific configuration."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Propagate to root handler
        logger.propagate = True
    return logger

@contextmanager
def timed_operation(logger: Optional[logging.Logger] = None):
    """Context manager to log execution time."""
    start = time.time()
    logger = logger or get_logger(__name__)
    try:
        yield
    finally:
        duration = time.time() - start
        logger.info(f"Operation completed in {duration:.2f}s")

@contextmanager
def error_handler(operation_name: str, logger: Optional[logging.Logger] = None):
    """Context manager to catch and log errors."""
    logger = logger or get_logger(__name__)
    try:
        yield
    except LLMRefactoringError as e:
        logger.error(f"Error in {operation_name}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in {operation_name}: {e}")
        raise
