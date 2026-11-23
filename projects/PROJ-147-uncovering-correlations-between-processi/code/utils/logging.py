"""
Logging utilities for the pipeline.
"""
import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import json
from datetime import datetime

from code.config import LOGS_DIR

_logger_instance: Optional[logging.Logger] = None

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger for the pipeline.
    """
    global _logger_instance
    if _logger_instance:
        return _logger_instance

    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()

    # Ensure log directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    log_path = Path(log_file) if log_file else LOGS_DIR / "pipeline.log"

    # File handler with rotation
    fh = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=3)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    _logger_instance = logger
    return logger

def get_logger() -> logging.Logger:
    """
    Get the configured logger instance.
    """
    if _logger_instance is None:
        return setup_logging()
    return _logger_instance

def log_warning_structured(message: str, context: Dict[str, Any] = None) -> None:
    """
    Log a warning with structured context if available.
    """
    logger = get_logger()
    if context:
        logger.warning(f"{message} | Context: {json.dumps(context)}")
    else:
        logger.warning(message)
