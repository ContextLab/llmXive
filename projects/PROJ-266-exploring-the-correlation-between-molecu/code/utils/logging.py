import logging
import sys
from pathlib import Path
from typing import Optional
from .config import get_project_root

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    """
    logger_name = name or __name__
    return logging.getLogger(logger_name)

def configure_root_logger(level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger for the project.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Avoid adding handlers multiple times if called repeatedly
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    
    return root_logger

def get_log_path() -> Path:
    """
    Get the path to the logs directory.
    """
    project_root = get_project_root()
    logs_path = project_root / 'logs'
    logs_path.mkdir(exist_ok=True)
    return logs_path

def setup_logging_for_script(script_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging specific to a script execution.
    """
    logger = get_logger(script_name)
    logger.setLevel(level)
    
    if not logger.handlers:
        log_dir = get_log_path()
        log_file = log_dir / f"{script_name}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Also log to console for immediate feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger
