import logging
import sys
from pathlib import Path
from typing import Optional

logger = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    global logger
    if logger is None:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    return logger

def log_info(msg: str):
    get_logger().info(msg)

def log_warning(msg: str):
    get_logger().warning(msg)

def log_error(msg: str):
    get_logger().error(msg)

def log_debug(msg: str):
    get_logger().debug(msg)

def setup_logging(log_file: Optional[str] = None):
    if log_file:
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        get_logger().addHandler(handler)
