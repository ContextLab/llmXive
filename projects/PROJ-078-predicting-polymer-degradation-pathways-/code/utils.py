import logging
import os
import time
from pathlib import Path
from typing import Optional, Callable, Any, Dict
import random

# Configure basic logging if not already configured
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup shared logging infrastructure with file handlers.
    
    Args:
        log_file: Optional path to log file.
        level: Logging level (default: INFO).
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger('llmXive')
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__).
        
    Returns:
        Logger instance.
    """
    return logging.getLogger(name)

def load_config_env(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from environment variables and optional file.
    
    Args:
        config_path: Optional path to config file (YAML/JSON).
        
    Returns:
        Dictionary of configuration values.
    """
    config = {}
    
    # Load from environment variables
    for key, value in os.environ.items():
        if key.startswith('LLMXIVE_'):
            config[key] = value
    
    # Override with file if provided
    if config_path and os.path.exists(config_path):
        import json
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            logging.warning(f"Failed to load config from {config_path}: {e}")
    
    return config

def get_project_paths() -> Dict[str, Path]:
    """
    Get standard project directory paths relative to the project root.
    
    Returns:
        Dictionary mapping path names to Path objects.
    """
    # Assume project root is 3 levels up from this file (code/utils.py)
    base_dir = Path(__file__).resolve().parent.parent
    
    return {
        'root': base_dir,
        'code': base_dir / 'code',
        'data_raw': base_dir / 'data' / 'raw',
        'data_processed': base_dir / 'data' / 'processed',
        'data_reports': base_dir / 'data' / 'reports',
        'tests': base_dir / 'tests',
        'state': base_dir / 'state'
    }

def retry_with_backoff(func: Callable, *args, max_retries: int = 3, base_delay: float = 1.0, **kwargs) -> Any:
    """
    Execute a function with exponential backoff on failure.
    
    Args:
        func: Function to execute.
        *args: Positional arguments for the function.
        max_retries: Maximum number of retry attempts (default: 3).
        base_delay: Base delay in seconds (default: 1.0).
        **kwargs: Keyword arguments for the function.
        
    Returns:
        Result of the function call.
        
    Raises:
        Exception: If all retries fail.
    """
    last_exception = None
    
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt == max_retries:
                break
            
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
            logging.warning(f"Attempt {attempt}/{max_retries} failed: {e}. Retrying in {delay:.2f}s...")
            time.sleep(delay)
    
    raise last_exception
