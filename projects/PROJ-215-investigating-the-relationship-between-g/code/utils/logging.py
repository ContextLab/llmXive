import logging
import os
from pathlib import Path
from typing import Optional

from code.config import LOGS_DIR

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging infrastructure.
    
    Args:
        log_file: Optional relative path to log file (e.g., "pipeline.log"). 
                  Defaults to LOGS_DIR/pipeline.log if not provided.
        level: Logging level (default: INFO).
    
    Returns:
        The root logger configured.
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates on re-run
    if logger.handlers:
        logger.handlers.clear()
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    if log_file is None:
        log_file = "pipeline.log"
    
    log_path = Path(log_file)
    if not log_path.is_absolute():
        log_path = LOGS_DIR / log_file
    
    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger instance. If name is provided, returns a named logger.
    Otherwise returns the root logger (which is configured by setup_logging).
    """
    if name:
        logger = logging.getLogger(name)
    else:
        logger = logging.getLogger()
    
    # If not configured yet, configure it
    if not logger.handlers:
        setup_logging(level=level)
    
    logger.setLevel(level)
    return logger
