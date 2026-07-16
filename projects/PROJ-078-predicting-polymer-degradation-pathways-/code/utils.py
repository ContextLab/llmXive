import logging
import os
import time
import random
from pathlib import Path
from typing import Optional, Callable, Any, TypeVar, Union

T = TypeVar('T')

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: The logging level (e.g., logging.INFO).
        log_file: Optional path to a log file. If None, logs to console only.
    """
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)
    
    # File handler if specified
    if log_file:
        # Ensure directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    for handler in handlers:
        root_logger.addHandler(handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: The name of the logger (usually __name__).
        
    Returns:
        A configured Logger instance.
    """
    return logging.getLogger(name)

def with_exponential_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> Callable[..., T]:
    """
    Decorator that implements exponential backoff for a function.
    
    Args:
        func: The function to wrap.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        
    Returns:
        The wrapped function.
    """
    def wrapper(*args, **kwargs) -> T:
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == max_retries:
                    break
                
                # Calculate delay with exponential backoff and jitter
                delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                logger = get_logger(func.__module__)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
        
        raise last_exception

def load_config(config_path: Optional[str] = None) -> dict:
    """
    Load configuration from a YAML file or environment variables.
    
    Args:
        config_path: Path to the YAML config file. If None, uses environment variables.
        
    Returns:
        Dictionary containing configuration.
    """
    import yaml
    
    config = {}
    
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
    
    # Override with environment variables if present
    # Example: DATA_RAW_PATH, DATA_PROCESSED_PATH, etc.
    env_mapping = {
        'DATA_RAW_PATH': 'data_raw_path',
        'DATA_PROCESSED_PATH': 'data_processed_path',
        'LOG_FILE': 'log_file',
        'LOG_LEVEL': 'log_level'
    }
    
    for env_key, config_key in env_mapping.items():
        env_val = os.getenv(env_key)
        if env_val:
            config[config_key] = env_val
    
    return config
