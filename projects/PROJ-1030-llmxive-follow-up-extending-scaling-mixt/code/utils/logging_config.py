import logging
import os
import sys
from pathlib import Path
from typing import Optional
import traceback
import time

# Ensure log directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configure root logger
def configure_root_logger():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # File handler
    file_handler = logging.FileHandler(LOG_DIR / "pipeline.log")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    configure_root_logger()
    logger = logging.getLogger(name)
    return logger

def fail_loudly(logger: logging.Logger, message: str, exception: Optional[Exception] = None) -> None:
    """
    Log a critical error with full context and traceback, then raise a RuntimeError.
    
    This function implements the "FAIL LOUDLY" principle:
    1. Logs the error at CRITICAL level
    2. Includes full traceback if an exception is provided
    3. Raises a RuntimeError to ensure the failure is not silently caught
    
    Args:
        logger: The logger instance to use
        message: The error message
        exception: Optional exception instance to include in the log
    
    Raises:
        RuntimeError: Always raised after logging to ensure failure is visible
    """
    full_message = f"FATAL ERROR: {message}"
    
    if exception:
        full_message += f"\nException: {type(exception).__name__}: {str(exception)}"
        full_message += f"\nTraceback:\n{''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))}"
    
    logger.critical(full_message)
    
    # Always raise to ensure the failure is not silently handled
    raise RuntimeError(full_message) from exception

class DataFetchLogger:
    """Specialized logger for data fetching operations with fail-loudly semantics."""
    
    def __init__(self, name: str = "data_fetch"):
        self.logger = get_logger(name)
        self.fetch_count = 0
        self.failure_count = 0
        self.start_time = None
    
    def start_fetch(self, source: str):
        """Log the start of a data fetch operation."""
        self.start_time = time.time()
        self.fetch_count += 1
        self.logger.info(f"Starting data fetch from: {source}")
    
    def success(self, source: str, size_bytes: int, elapsed: float):
        """Log a successful data fetch."""
        self.logger.info(
            f"Successfully fetched {size_bytes:,} bytes from {source} "
            f"in {elapsed:.2f}s (Total fetches: {self.fetch_count})"
        )
    
    def failure(self, source: str, error: Exception, retry_count: int = 0):
        """Log a data fetch failure with full context."""
        self.failure_count += 1
        self.logger.warning(
            f"Data fetch failed from {source} (Attempt {retry_count + 1}): {str(error)}"
        )
    
    def fail_loudly(self, source: str, error: Exception, context: str = ""):
        """
        Log a critical data fetch failure and raise an exception.
        
        This is the primary entry point for "FAIL LOUDLY" behavior in data fetching.
        It ensures that:
        1. All failure context is logged
        2. The exception is raised to stop execution
        3. No synthetic fallback is attempted
        
        Args:
            source: The data source that failed
            error: The exception that occurred
            context: Additional context about the failure
        """
        message = f"Data fetch from {source} failed permanently"
        if context:
            message += f": {context}"
        
        fail_loudly(self.logger, message, error)
    
    def get_stats(self) -> dict:
        """Return fetch statistics."""
        return {
            "total_fetches": self.fetch_count,
            "failures": self.failure_count,
            "success_rate": (self.fetch_count - self.failure_count) / max(1, self.fetch_count)
        }

def configure_data_fetch_logger() -> DataFetchLogger:
    """Create and return a configured DataFetchLogger instance."""
    return DataFetchLogger("data_fetch")

# Initialize root logger on module import
configure_root_logger()
