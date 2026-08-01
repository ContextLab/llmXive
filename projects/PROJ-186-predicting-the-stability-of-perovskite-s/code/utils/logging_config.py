"""
code/utils/logging_config.py

Configures the logging infrastructure for the pipeline.
"""
import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "pipeline.log"

def get_logger(name: str) -> logging.Logger:
    """
    Gets a logger with the specified name, configured to write to the pipeline log.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # File handler
    fh = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def log_exclusion_reason(source: str, item_id: str, reason: str):
    """
    Logs a specific exclusion reason to the pipeline log.
    """
    logger = get_logger(source)
    logger.warning(f"EXCLUSION [Source: {source}, ID: {item_id}]: {reason}")

def log_pipeline_event(source: str, message: str):
    """
    Logs a general pipeline event.
    """
    logger = get_logger(source)
    logger.info(f"PIPELINE EVENT: {message}")
