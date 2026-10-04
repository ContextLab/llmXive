import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union, List, TYPE_CHECKING
import json
from datetime import datetime

if TYPE_CHECKING:
    from typing import Dict as DictType

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def ensure_log_dir():
    LOG_DIR.mkdir(exist_ok=True)

class PIIFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = record.msg.replace("secret_key", "****")
        return True

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    file_handler = logging.FileHandler(LOG_DIR / f"{name}.log")
    file_handler.setLevel(logging.ERROR)
    file_handler.addFilter(PIIFilter())
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

def get_model_fallback_logger() -> logging.Logger:
    return get_logger("model_fallback")

def log_model_switch(logger: logging.Logger, from_model: str, to_model: str):
    logger.info(f"Model switched from {from_model} to {to_model} due to constraints.")

def log_memory_error(logger: logging.Logger, error_msg: str):
    logger.error(f"Memory error encountered: {error_msg}")

def log_fallback_success(logger: logging.Logger, model_name: str):
    logger.info(f"Fallback to {model_name} successful.")

def log_fallback_failure(logger: logging.Logger, error_msg: str):
    logger.error(f"Fallback failed: {error_msg}")

def log_acquisition_failure(logger: logging.Logger, venue: str, error: str):
    logger.error(f"Data acquisition failed for venue {venue}: {error}")

def log_preprocessing_rejection(logger: logging.Logger, reason: str):
    logger.warning(f"Preprocessing rejected entry: {reason}")

def log_preprocessing_rejection_count(logger: logging.Logger, count: int):
    logger.info(f"Total entries rejected during preprocessing: {count}")

def sanitize_structured_log(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize structured log data to remove PII or sensitive info."""
    if not isinstance(data, dict):
        return data
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, dict):
            sanitized[key] = sanitize_structured_log(value)
        elif isinstance(value, str):
            if "secret" in key.lower() or "password" in key.lower():
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        else:
            sanitized[key] = value
    return sanitized

def initialize_pipeline_logging():
    ensure_log_dir()
    get_logger("pipeline")

def log_data_source_check(logger: logging.Logger, source: str, status: str):
    logger.info(f"Data source check for {source}: {status}")
