import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import traceback
import psutil

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

_logger: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        if not _logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            _logger.addHandler(handler)
            _logger.setLevel(logging.INFO)
    return _logger

def setup_logging(level: int = logging.INFO) -> None:
    global _logger
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(level)
    if not _logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        _logger.addHandler(handler)

def log_error_and_raise(error: Exception, logger: logging.Logger) -> None:
    logger.error(f"Error occurred: {str(error)}")
    logger.debug(traceback.format_exc())
    raise error

def safe_execute(func, logger: logging.Logger, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_error_and_raise(e, logger)

def log_duration(func):
    def wrapper(*args, **kwargs):
        logger = kwargs.get("logger") or get_logger()
        start = datetime.now()
        result = func(*args, **kwargs)
        duration = (datetime.now() - start).total_seconds()
        logger.info(f"{func.__name__} completed in {duration:.2f}s")
        return result
    return wrapper

def check_memory_usage(threshold_gb: float = 6.0) -> bool:
    """Check if current memory usage exceeds threshold. Returns True if over threshold."""
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / (1024 ** 3)
    if mem_gb > threshold_gb:
        return True
    return False
