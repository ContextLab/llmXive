import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class ParseError(PipelineError):
    """Exception raised when parsing fails."""
    pass

class TimeoutError(PipelineError):
    """Exception raised when a timeout occurs."""
    pass

class OOMError(PipelineError):
    """Exception raised when out of memory occurs."""
    pass

class NetworkError(PipelineError):
    """Exception raised when network operations fail."""
    pass

class ChunkContext:
    """Context manager for tracking chunk processing."""
    
    def __init__(self, chunk_id: str, logger: logging.Logger):
        self.chunk_id = chunk_id
        self.logger = logger
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting processing for chunk: {self.chunk_id}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"Completed chunk {self.chunk_id} in {duration:.2f}s")
        else:
            self.logger.error(f"Failed chunk {self.chunk_id} after {duration:.2f}s: {exc_val}")
        
        return False

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name. Defaults to module name if not provided.
        
    Returns:
        Configured logger instance.
    """
    if name is None:
        frame = sys._getframe(1)
        name = frame.f_globals.get('__name__', 'unknown')
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger

def retry_on_transient_errors(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator to retry functions on transient errors.
    
    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay between retries in seconds.
        
    Returns:
        Decorated function.
    """
    import time
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (NetworkError, TimeoutError, ConnectionError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logging.getLogger(func.__module__).warning(
                            f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logging.getLogger(func.__module__).error(
                            f"All {max_retries} attempts failed for {func.__name__}"
                        )
            
            raise last_exception
        
        return wrapper
    
    return decorator

def handle_parse_error(error: Exception, chunk_id: str, logger: logging.Logger) -> None:
    """Handle and log parse errors."""
    logger.error(f"Parse error for chunk {chunk_id}: {str(error)}")
    logger.debug(traceback.format_exc())

def handle_timeout_error(error: Exception, chunk_id: str, logger: logging.Logger) -> None:
    """Handle and log timeout errors."""
    logger.error(f"Timeout error for chunk {chunk_id}: {str(error)}")
    logger.debug(traceback.format_exc())

def handle_oom_error(error: Exception, chunk_id: str, logger: logging.Logger) -> None:
    """Handle and log OOM errors."""
    logger.error(f"OOM error for chunk {chunk_id}: {str(error)}")
    logger.debug(traceback.format_exc())

def handle_network_error(error: Exception, chunk_id: str, logger: logging.Logger) -> None:
    """Handle and log network errors."""
    logger.error(f"Network error for chunk {chunk_id}: {str(error)}")
    logger.debug(traceback.format_exc())

def main():
    """Main entry point for logging utilities demonstration."""
    logger = get_logger("logging_utils")
    logger.info("Logging utilities module loaded successfully")
    logger.info("Available error classes: PipelineError, ParseError, TimeoutError, OOMError, NetworkError")
    logger.info("Available functions: get_logger, retry_on_transient_errors, handle_*_error")

if __name__ == "__main__":
    main()