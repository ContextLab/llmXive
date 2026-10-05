import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from config import get_config, Config

logger: Optional[logging.Logger] = None

def initialize_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    global logger
    if logger is not None:
        return

    logger = logging.getLogger("llmxive")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler if specified
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

def get_logger() -> logging.Logger:
    global logger
    if logger is None:
        initialize_logging()
    return logger

def debug(msg: str, *args, **kwargs):
    get_logger().debug(msg, *args, **kwargs)

def info(msg: str, *args, **kwargs):
    get_logger().info(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs):
    get_logger().warning(msg, *args, **kwargs)

def error(msg: str, *args, **kwargs):
    get_logger().error(msg, *args, **kwargs)

def critical(msg: str, *args, **kwargs):
    get_logger().critical(msg, *args, **kwargs)
