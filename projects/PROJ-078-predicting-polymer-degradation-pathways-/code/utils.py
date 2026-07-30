import logging
import os
import time
from pathlib import Path
from typing import Optional, Callable, Any, Dict
import random

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_str: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration with optional file handler.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Optional path to log file
        format_str: Optional log format string
    
    Returns:
        Root logger instance
    """
    if format_str is None:
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(format_str))
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(format_str))
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def load_config_env(
    config_path: Optional[str] = None,
    env_prefix: str = "POLYMER_"
) -> Dict[str, Any]:
    """
    Load configuration from environment variables and optional config file.
    
    Args:
        config_path: Optional path to YAML/JSON config file
        env_prefix: Prefix for environment variables
    
    Returns:
        Configuration dictionary
    """
    config = {}
    
    # Load from config file if provided
    if config_path:
        config_path = Path(config_path)
        if config_path.exists():
            if config_path.suffix == '.yaml' or config_path.suffix == '.yml':
                try:
                    import yaml
                    with open(config_path, 'r') as f:
                        file_config = yaml.safe_load(f)
                        config.update(file_config or {})
                except ImportError:
                    get_logger(__name__).warning("PyYAML not installed, skipping YAML config")
            elif config_path.suffix == '.json':
                import json
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
    
    # Override with environment variables
    for key, value in os.environ.items():
        if key.startswith(env_prefix):
            config_key = key[len(env_prefix):].lower()
            config[config_key] = value
    
    return config

def get_project_paths() -> Any:
    """
    Get project root and key directory paths.
    
    Returns:
        Simple namespace with path attributes
    """
    # Assume project root is parent of 'code' directory
    current_dir = Path(__file__).parent
    root = current_dir.parent
    
    class Paths:
        def __init__(self, root):
            self.root = root
            self.code = root / "code"
            self.data_raw = root / "data" / "raw"
            self.data_processed = root / "data" / "processed"
            self.data_reports = root / "data" / "reports"
            self.tests = root / "tests"
            self.state = root / "state"
            self.specs = root / "specs"
    
    return Paths(root)

def retry_with_backoff(
    func: Callable,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retries
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Factor to multiply delay by
        exceptions: Tuple of exceptions to catch and retry
    
    Returns:
        Result of func
    
    Raises:
        Last exception if all retries fail
    """
    logger = get_logger(__name__)
    delay = base_delay
    
    for attempt in range(max_retries):
        try:
            return func()
        except exceptions as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                raise
            
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            time.sleep(delay + random.uniform(0, 0.1 * delay))  # Add jitter
            delay = min(delay * backoff_factor, max_delay)
    
    # Should never reach here, but just in case
    raise RuntimeError("Retry loop exited without returning")