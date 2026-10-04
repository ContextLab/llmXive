import logging
import sys
from pathlib import Path
from typing import Optional
from .config import get_project_root

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance.
    """
    return logging.getLogger(name)

def configure_root_logger(level: int = logging.INFO) -> None:
    """
    Configure the root logger for the application.
    """
    if not logging.getLogger().handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(level)

def get_log_path() -> Path:
    """
    Get the path to the logs directory.
    """
    return get_project_root() / 'logs'

def setup_logging_for_script(script_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging for a specific script, ensuring logs go to a file in the logs directory.
    """
    log_dir = get_log_path()
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"{script_name}.log"
    
    logger = logging.getLogger(script_name)
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)
        
        # Also add a console handler for immediate feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '%(levelname)s: %(message)s'
        ))
        logger.addHandler(console_handler)
    
    return logger
