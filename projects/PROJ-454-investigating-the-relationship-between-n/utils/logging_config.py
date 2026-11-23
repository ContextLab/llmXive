"""
utils/logging_config.py
Centralized logging configuration.
Includes resource logging support for T017.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_general_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """Setup a general logger with console and file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler
    if log_file is None:
        log_file = LOG_DIR / f"{name}.log"
    
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

def setup_resource_logger():
    """Setup a dedicated logger for resource monitoring."""
    return setup_general_logger("resource_monitor", log_file=LOG_DIR / "resource_usage.log")

def log_resource_usage():
    """Wrapper to log resource usage."""
    from utils.resource_monitor import log_resource_snapshot
    log_resource_snapshot()

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return setup_general_logger(name)

def initialize_project_logging():
    """Initialize project-wide logging."""
    setup_general_logger("project_root")
    setup_resource_logger()
    logging.info("Project logging initialized.")
