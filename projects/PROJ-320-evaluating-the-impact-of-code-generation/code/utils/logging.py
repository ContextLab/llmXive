"""
Logging infrastructure with file rotation for data and reports directories.
"""
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

_logger_instance = None
_setup_done = False

def setup_logging(log_dir: Optional[Path] = None, level: int = logging.INFO) -> None:
    """
    Initialize logging infrastructure.
    
    Args:
        log_dir: Directory for log files. Defaults to project_root/logs/
        level: Logging level (default: INFO)
    """
    global _setup_done
    if _setup_done:
        return
    
    if log_dir is None:
        # Default to project root logs directory
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / 'logs'
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    log_file = log_dir / 'pipeline.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    _setup_done = True

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    global _logger_instance
    if _logger_instance is None:
        # Ensure setup is done
        setup_logging()
        _logger_instance = logging.getLogger(name)
    
    # Return a named logger for the specific module
    return logging.getLogger(name)
