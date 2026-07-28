import logging
import sys
from pathlib import Path
from typing import Optional
import os

# Import config to get project root if needed, but keep it minimal for setup
# We define a simple fallback for get_project_root if config isn't fully ready yet
def _get_project_root():
    return Path(__file__).resolve().parent.parent.parent

def get_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO):
    """
    Retrieves or creates a logger with the specified name.
    
    Args:
        name: Name of the logger (usually __name__).
        log_file: Optional path to a log file.
        level: Logging level (default: INFO).
        
    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        # Logger already configured
        return logger
    
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO):
    """
    Sets up the root logger configuration for the entire project.
    
    Args:
        log_file: Optional path to a log file.
        level: Logging level.
    """
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
        
    root_logger.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def get_logger_level():
    """
    Returns the current logging level of the root logger.
    """
    return logging.getLogger().getEffectiveLevel()