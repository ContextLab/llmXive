import logging
import time
import random
import os
import sys
from typing import Callable, Type, TypeVar, Optional, List
from functools import wraps

# Custom Exceptions
class DataFetchError(Exception):
    """Raised when data fetching fails after all retry attempts."""
    pass

class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass

class PhysicsSimError(Exception):
    """Raised when physics simulation fails."""
    pass

T = TypeVar('T')

def retry_with_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        exponential_base: Base for exponential calculation.
        jitter: If True, adds random jitter to delay.
        exceptions: Tuple of exception types to catch and retry.
        
    Returns:
        The decorated function.
        
    Raises:
        The original exception if max retries are exceeded.
        DataFetchError if the failure is related to data fetching.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Max retries exceeded, fail loudly
                        logger = logging.getLogger(__name__)
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {str(e)}")
                        
                        # Convert to DataFetchError if it looks like a fetch issue
                        if isinstance(e, (DataFetchError, ConnectionError, TimeoutError)):
                            raise DataFetchError(f"Data fetch failed permanently after {max_retries} retries: {str(e)}") from e
                        else:
                            raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter if enabled
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_exception
        return wrapper
    return decorator

def validate_config(config: dict, required_keys: List[str]) -> None:
    """
    Validate that a configuration dictionary contains all required keys.
    
    Args:
        config: Configuration dictionary to validate.
        required_keys: List of required key names.
        
    Raises:
        ConfigError: If any required key is missing.
    """
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ConfigError(f"Missing required configuration keys: {missing_keys}")

def handle_simulation_failure(error: Exception, context: Optional[str] = None) -> None:
    """
    Handle physics simulation failures with appropriate logging.
    
    Args:
        error: The exception that occurred.
        context: Optional context about what was being simulated.
        
    Raises:
        PhysicsSimError: Always raised after logging.
    """
    logger = logging.getLogger(__name__)
    message = f"Physics simulation failed"
    if context:
        message += f" during {context}"
    message += f": {str(error)}"
    
    logger.error(message, exc_info=True)
    raise PhysicsSimError(message) from error

class DataFetchHandler:
    """
    Handler class for managing data fetch operations with retry logic.
    """
    
    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.logger = logging.getLogger(__name__)
    
    @retry_with_backoff(
        max_retries=5,
        base_delay=1.0,
        max_delay=60.0
    )
    def fetch_data(self, url: str, destination: str, **kwargs) -> bool:
        """
        Fetch data from a URL with exponential backoff retry logic.
        
        Args:
            url: Source URL for the data.
            destination: Local path to save the data.
            **kwargs: Additional arguments passed to the fetch function.
            
        Returns:
            True if fetch was successful.
            
        Raises:
            DataFetchError: If all retry attempts fail.
        """
        import urllib.request
        import ssl
        
        # Create SSL context that doesn't verify certificates (for testing)
        # In production, this should be properly configured
        ssl_context = ssl.create_default_context()
        
        # Attempt to fetch the data
        try:
            self.logger.info(f"Fetching data from {url} to {destination}")
            
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            # Use urllib to fetch the data
            urllib.request.urlretrieve(url, destination, reporthook=self._progress_hook)
            
            self.logger.info(f"Successfully fetched data to {destination}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fetch data from {url}: {str(e)}")
            raise DataFetchError(f"Failed to fetch data from {url}: {str(e)}") from e
    
    def _progress_hook(self, block_num, block_size, total_size):
        """
        Progress hook for urllib.urlretrieve.
        
        Args:
            block_num: Current block number.
            block_size: Size of each block.
            total_size: Total size of the file.
        """
        if total_size > 0:
            downloaded = block_num * block_size
            percentage = min(100, (downloaded / total_size) * 100)
            if block_num % 10 == 0:  # Log every 10 blocks to avoid spam
                self.logger.debug(f"Download progress: {percentage:.1f}%")