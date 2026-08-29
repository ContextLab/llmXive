"""
Structured logging utilities for the pipeline.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger_instance = None

def get_logger(name: str = "llmxive") -> logging.Logger:
    """Get or create the global logger instance."""
    global logger_instance
    if logger_instance is None:
        logger_instance = logging.getLogger(name)
        logger_instance.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        
        # File handler
        log_file = LOG_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        
        if not logger_instance.handlers:
            logger_instance.addHandler(console_handler)
            logger_instance.addHandler(file_handler)
    
    return logger_instance

def log_info(msg: str):
    logger = get_logger()
    logger.info(msg)

def log_warning(msg: str):
    logger = get_logger()
    logger.warning(msg)

def log_error(msg: str):
    logger = get_logger()
    logger.error(msg)

def log_debug(msg: str):
    logger = get_logger()
    logger.debug(msg)
