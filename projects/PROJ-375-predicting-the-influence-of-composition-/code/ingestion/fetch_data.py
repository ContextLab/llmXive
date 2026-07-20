"""
T008: Fail Loud Loader pattern and logging setup.
"""
import logging
import sys
from pathlib import Path
from typing import Callable, Any

def setup_logging() -> logging.Logger:
    """Configures logging to file and stdout."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # File handler
        fh = logging.FileHandler(log_dir / "pipeline.log")
        fh.setLevel(logging.INFO)
        
        # Stream handler
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        sh.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(sh)
    
    return logger

def fail_loud_loader(func: Callable) -> Callable:
    """
    Decorator to ensure a loader fails loudly if data is not found.
    """
    def wrapper(*args, **kwargs) -> Any:
        try:
            result = func(*args, **kwargs)
            if result is None:
                raise ValueError("Loader returned None. Data fetch failed.")
            if isinstance(result, list) and len(result) == 0:
                raise ValueError("Loader returned empty list. No data found.")
            return result
        except Exception as e:
            logging.error(f"Data loading failed loudly: {e}")
            raise
    return wrapper