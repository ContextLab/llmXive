"""
Logging and error handling utilities.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import time
import resource

class PipelineError(Exception):
    pass

class DataIngestionError(PipelineError):
    pass

class AlignmentError(PipelineError):
    pass

class AnalysisError(PipelineError):
    pass

class ConfigError(PipelineError):
    pass

class ValidationError(PipelineError):
    pass

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def setup_logging(log_file: Optional[Path] = None):
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logging.root.addHandler(handler)

def log_duration(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger = get_logger(func.__module__)
        logger.info(f"{func.__name__} completed in {end - start:.2f} seconds")
        return result
    return wrapper

def check_memory_usage() -> float:
    """Check current memory usage in GB."""
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # On Linux, ru_maxrss is in KB; on macOS, it's in bytes
    if sys.platform == 'darwin':
        usage_gb = usage / (1024 ** 3)
    else:
        usage_gb = usage / (1024 * 1024)
    return usage_gb

def log_error_and_raise(error_type: type, message: str):
    logger = get_logger(__name__)
    logger.error(message)
    raise error_type(message)

def safe_execute(func, *args, **kwargs):
    try:
        return func(*args, **kwargs), None
    except Exception as e:
        return None, e
