"""Logging configuration for the pipeline."""
import logging
import sys
import os
from pathlib import Path
from typing import Optional
from utils.error_handlers import ConfigurationError

def setup_logging(log_level: str = "INFO", log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"):
    """Set up the root logger."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

def init_project_logger(log_file: Optional[str] = None) -> logging.Logger:
    """Initialize a project logger with file output if specified."""
    logger = logging.getLogger("solder_pipeline")
    logger.setLevel(logging.DEBUG)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
