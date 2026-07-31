import logging
import os
import time
from pathlib import Path
from typing import Optional, Callable, Any, Dict
import random

def setup_logging(log_file_name: str = "pipeline") -> tuple:
    """
    Setup logging configuration with file and console handlers.
    
    Args:
        log_file_name: Base name for log files (without extension)
        
    Returns:
        Tuple of (log_file_path, logger_instance)
    """
    log_dir = Path("data") / "reports"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"{log_file_name}.log"
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return log_file, logger

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def load_config_env() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Dictionary of configuration values
    """
    config = {
        'project_root': os.getenv('PROJECT_ROOT', str(Path.cwd())),
        'data_path': os.getenv('DATA_PATH', 'data'),
        'code_path': os.getenv('CODE_PATH', 'code'),
        'state_path': os.getenv('STATE_PATH', 'state'),
        'rate_limit_delay': float(os.getenv('RATE_LIMIT_DELAY', '1.0')),
        'max_retries': int(os.getenv('MAX_RETRIES', '5')),
    }
    return config

def get_project_paths() -> Path:
    """
    Get the project root path.
    
    Returns:
        Path object for project root
    """
    return Path.cwd()

def retry_with_backoff(
    func: Callable,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    logger: Optional[logging.Logger] = None
) -> Any:
    """
    Execute a function with exponential backoff retry logic.
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        logger: Logger instance (optional)
        
    Returns:
        Result of the function call
        
    Raises:
        Exception: If all retries fail
    """
    if logger is None:
        logger = get_logger()
    
    attempt = 0
    delay = base_delay
    
    while attempt < max_retries:
        try:
            return func()
        except Exception as e:
            attempt += 1
            if attempt == max_retries:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                raise
            
            jitter = random.uniform(0, 0.1 * delay)
            actual_delay = min(delay + jitter, max_delay)
            
            logger.warning(
                f"Attempt {attempt}/{max_retries} failed: {e}. "
                f"Retrying in {actual_delay:.2f}s"
            )
            time.sleep(actual_delay)
            delay *= 2
    
    raise Exception("Unexpected retry logic failure")
