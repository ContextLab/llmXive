import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from config import ensure_directories

LOG_DIR = "data/logs"
LOG_FILE_NAME = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

_logger_instance: Optional[logging.Logger] = None

def setup_logging(log_dir: Optional[str] = None) -> None:
    """
    Configure logging to output to both console and file.
    
    Args:
        log_dir: Optional directory for log files. Defaults to LOG_DIR.
    """
    global _logger_instance
    if _logger_instance is not None:
        return  # Already configured

    target_dir = log_dir if log_dir else LOG_DIR
    ensure_directories(target_dir)
    
    log_path = os.path.join(target_dir, LOG_FILE_NAME)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    _logger_instance = root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    Initializes logging configuration if not already done.
    
    Args:
        name: Logger name (usually module name)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    setup_logging()
    return logging.getLogger(name)
