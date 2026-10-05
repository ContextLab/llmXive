import logging
import os
import time
import random
from pathlib import Path
from typing import Optional, Callable, Any, Dict, Tuple
from datetime import datetime

# Global logger instance
_logger: Optional[logging.Logger] = None

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure and return the project logger."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger("llmXive")
        _logger.setLevel(level)
        
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch.setFormatter(formatter)
        
        # Add handler to logger
        if not _logger.handlers:
            _logger.addHandler(ch)
    
    return _logger

def get_logger() -> logging.Logger:
    """Get the configured logger instance."""
    if _logger is None:
        return setup_logging()
    return _logger

def load_config_env(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from environment variables and optional file."""
    config = {}
    
    # Load from file if provided
    if config_path and config_path.exists():
        # Simple key=value parser for .env style files
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    # Override with environment variables
    for key in list(config.keys()):
        if key in os.environ:
            config[key] = os.environ[key]
    
    return config

def get_project_paths(base_dir: Optional[Path] = None) -> Dict[str, Path]:
    """Return standard project directory paths."""
    if base_dir is None:
        # Default to parent of code directory if running from code/
        base_dir = Path(__file__).resolve().parent.parent
    
    return {
        'root': base_dir,
        'code': base_dir / 'code',
        'data_raw': base_dir / 'data' / 'raw',
        'data_processed': base_dir / 'data' / 'processed',
        'data_reports': base_dir / 'data' / 'reports',
        'tests': base_dir / 'tests',
        'state': base_dir / 'state',
        'state_projects': base_dir / 'state' / 'projects'
    }

def exponential_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> Callable:
    """Decorator for exponential backoff retry logic."""
    def wrapper(*args, **kwargs) -> Any:
        last_exception = None
        delay = base_delay
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger = get_logger()
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * 2 + random.uniform(0, 0.1), max_delay)
        
        raise last_exception
    return wrapper

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> Any:
    """Execute a function with exponential backoff."""
    logger = get_logger()
    last_exception = None
    delay = base_delay
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
                delay = min(delay * 2 + random.uniform(0, 0.1), max_delay)
    
    raise last_exception

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)

def get_timestamp() -> str:
    """Return current timestamp in ISO format."""
    return datetime.now().isoformat()
