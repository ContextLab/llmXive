"""
Structured logging utilities for the pipeline.
"""
import logging
import sys
from pathlib import Path

# Configure a global logger
logger = logging.getLogger("llmXive")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def get_logger(name: str = "llmXive") -> logging.Logger:
    """Returns a logger instance."""
    return logging.getLogger(name)

def log_info(msg: str):
    logger.info(msg)

def log_warning(msg: str):
    logger.warning(msg)

def log_error(msg: str):
    logger.error(msg)

def log_debug(msg: str):
    logger.debug(msg)
