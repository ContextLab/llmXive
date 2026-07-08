import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Ensure logs directory exists
LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOGS_DIR / "pipeline.log"

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger that writes to logs/pipeline.log.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # File handler
    file_handler = RotatingFileHandler(
        LOG_FILE, 
        maxBytes=10*1024*1024, 
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def log_exclusion_reason(material_id: str, reason: str):
    """
    Logs the reason for excluding a material from the dataset.
    """
    logger = get_logger(__name__)
    logger.warning(f"Excluding {material_id}: {reason}")

def log_pipeline_event(event: str):
    """
    Logs a high-level pipeline event.
    """
    logger = get_logger(__name__)
    logger.info(f"PIPELINE_EVENT: {event}")