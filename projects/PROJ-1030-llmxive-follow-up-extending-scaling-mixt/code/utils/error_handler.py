import logging
import time
from typing import Callable, Type, TypeVar, Optional, List
from functools import wraps
import random
import os
from utils.logging_config import get_logger, fail_loudly, DataFetchLogger

T = TypeVar('T')

class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class PhysicsSimError(Exception):
    """Custom exception for physics simulation errors."""
    pass

def retry_with_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        jitter: Whether to add random jitter to delays
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            logger = get_logger(func.__module__)
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (DataFetchError, ConnectionError, TimeoutError, OSError) as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        fail_loudly(f"Data fetch failed after {max_retries} retries: {str(e)}", exception=e)
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    # Add jitter if enabled
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
            
            # Should never reach here due to fail_loudly, but safety net
            fail_loudly(f"Unexpected failure in {func.__name__}", exception=last_exception)
        return wrapper
    return decorator

def validate_config(config: dict) -> bool:
    """Validate configuration dictionary."""
    required_keys = ['data_source', 'output_path']
    for key in required_keys:
        if key not in config:
            raise ConfigError(f"Missing required config key: {key}")
    return True

def handle_simulation_failure(error: Exception, context: str = ""):
    """Handle physics simulation failures by logging and raising."""
    logger = get_logger(__name__)
    logger.error(f"Simulation failed in {context}: {str(error)}")
    raise PhysicsSimError(f"Simulation failed in {context}: {str(error)}") from error

class DataFetchHandler:
    """Handler class for managing data fetch operations with retry logic."""
    
    def __init__(self, logger_name: str = "data_fetch"):
        self.logger = DataFetchLogger.get_logger(logger_name)
        
    @retry_with_backoff(max_retries=5, base_delay=2.0, max_delay=30.0)
    def fetch_data(self, url: str, dest_path: str) -> bool:
        """
        Fetch data from URL with exponential backoff retry logic.
        
        Args:
            url: Source URL
            dest_path: Destination file path
            
        Returns:
            True if successful
            
        Raises:
            DataFetchError: If all retries fail
        """
        try:
            # Import here to avoid circular dependencies
            import urllib.request
            import ssl
            
            # Create SSL context that doesn't verify certificates (for testing)
            # In production, this should be properly configured
            ssl_context = ssl.create_default_context()
            # ssl_context.check_hostname = False
            # ssl_context.verify_mode = ssl.CERT_NONE
            
            self.logger.info(f"Fetching data from {url} to {dest_path}")
            
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            # Perform fetch
            urllib.request.urlretrieve(url, dest_path, context=ssl_context)
            
            if not os.path.exists(dest_path):
                raise DataFetchError(f"Download completed but file not found: {dest_path}")
            
            self.logger.info(f"Successfully fetched data to {dest_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fetch failed: {str(e)}")
            raise DataFetchError(f"Failed to fetch data from {url}", original_exception=e) from e
            
    def fetch_with_validation(self, url: str, dest_path: str, expected_size: Optional[int] = None) -> bool:
        """
        Fetch data with optional size validation.
        
        Args:
            url: Source URL
            dest_path: Destination file path
            expected_size: Optional expected file size in bytes
            
        Returns:
            True if successful and validated
        """
        success = self.fetch_data(url, dest_path)
        
        if success and expected_size is not None:
            actual_size = os.path.getsize(dest_path)
            if actual_size != expected_size:
                raise DataFetchError(
                    f"File size mismatch: expected {expected_size}, got {actual_size}"
                )
        
        return success