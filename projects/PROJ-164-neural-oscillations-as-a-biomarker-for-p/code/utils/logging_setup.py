import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from utils.config import LOGS, PROJECT_ID

def get_logger(name: str = __name__) -> logging.Logger:
    """Get a logger instance configured for the project."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler with rotation
    log_file = Path(LOGS) / "pipeline.log"
    os.makedirs(LOGS, exist_ok=True)
    fh = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

def log_mode_switch(mode: str):
    """Log a mode switch event."""
    logger = get_logger()
    logger.info(f"MODE SWITCH: {mode}")

def log_resource_usage():
    """Log current resource usage (placeholder for actual monitoring)."""
    logger = get_logger()
    # In a real implementation, this would query system resources
    logger.info("Resource usage logged (placeholder)")
