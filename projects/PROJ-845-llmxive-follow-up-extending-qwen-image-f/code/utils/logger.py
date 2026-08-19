import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

_loggers = {}

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger with the specified name.
    
    Args:
        name: Logger name
        log_file: Optional path to log file
        
    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Create logs directory
    logs_dir = os.path.join(project_root, "code", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    if log_file is None:
        log_file = os.path.join(logs_dir, "app.log")
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    # Also add console handler for debugging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    _loggers[name] = logger
    return logger
