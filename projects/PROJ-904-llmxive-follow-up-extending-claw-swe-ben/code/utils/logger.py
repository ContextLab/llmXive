import logging
import sys
import traceback
from pathlib import Path
from typing import Optional
from datetime import datetime
import json

class ResearchError(Exception):
    pass

class DataLoadError(ResearchError):
    pass

class ModelExecutionError(ResearchError):
    pass

class ConfigurationError(ResearchError):
    pass

class AnalysisError(ResearchError):
    pass

def setup_logger(name: str, log_file: Optional[str] = None, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def log_error(logger: logging.Logger, error: Exception, context: Optional[Dict] = None):
    error_info = {
        "type": type(error).__name__,
        "message": str(error),
        "traceback": traceback.format_exc(),
        "timestamp": datetime.utcnow().isoformat(),
        "context": context or {}
    }
    logger.error(json.dumps(error_info))

def safe_execute(func, logger: Optional[logging.Logger] = None, default: Any = None):
    try:
        return func()
    except Exception as e:
        if logger:
            log_error(logger, e)
        return default
