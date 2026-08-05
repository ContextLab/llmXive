import logging
import os
import time
from pathlib import Path
from typing import Optional, Callable, Any, Dict
import random

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger('llmXive')
    logger.setLevel(level)
    
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance."""
    if name:
        return logging.getLogger(f'llmXive.{name}')
    return logging.getLogger('llmXive')

def load_config_env(env_file: Optional[str] = None) -> Dict[str, str]:
    """Load environment variables from a file."""
    config = {}
    if env_file and os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
    return config

def get_project_paths() -> Dict[str, Path]:
    """Get project directory paths."""
    root = Path(__file__).parent.parent
    return {
        'root': root,
        'code': root / 'code',
        'data': root / 'data',
        'raw': root / 'data' / 'raw',
        'processed': root / 'data' / 'processed',
        'state': root / 'state',
        'reports': root / 'data' / 'reports',
        'tests': root / 'tests'
    }

def retry_with_backoff(func: Callable, max_retries: int = 3, base_delay: float = 1.0) -> Any:
    """Retry a function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
            time.sleep(delay)
    return None

# Initialize logger on module load
setup_logging()
