import logging
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

LOG_DIR = Path("logs")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def ensure_log_dir():
    """Ensure the log directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger configured to write to both console and a file.
    """
    ensure_log_dir()
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(ch)

        # File handler
        log_file = LOG_DIR / f"{name}.log"
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(fh)

    return logger

def get_model_fallback_logger() -> logging.Logger:
    """Get a specific logger for model fallback events."""
    return get_logger("model_fallback", logging.WARNING)

def log_model_switch(original_model: str, fallback_model: str, reason: str):
    """Log a model switch event."""
    logger = get_model_fallback_logger()
    logger.warning(
        f"Model switch triggered: {original_model} -> {fallback_model}. Reason: {reason}"
    )

def log_memory_error(memory_limit_mb: int, requested_mb: int):
    """Log a memory constraint error."""
    logger = get_model_fallback_logger()
    logger.error(
        f"Memory constraint hit: Limit {memory_limit_mb}MB, Requested {requested_mb}MB."
    )

def log_fallback_success(fallback_model: str):
    """Log successful fallback."""
    logger = get_model_fallback_logger()
    logger.info(f"Fallback to {fallback_model} successful.")

def log_fallback_failure(original_model: str, reason: str):
    """Log failed fallback."""
    logger = get_model_fallback_logger()
    logger.critical(f"Fallback failed for {original_model}: {reason}")

def initialize_pipeline_logging():
    """Initialize the main pipeline logger."""
    return get_logger("pipeline", logging.INFO)

def log_acquisition_failure(source: str, url: str, error: str):
    """
    Log a failure during data acquisition.
    Used by T015 to track fetch errors loudly.
    """
    logger = get_logger("data_acquisition", logging.ERROR)
    logger.error(f"Acquisition failed for source '{source}' at '{url}': {error}")

def log_preprocessing_rejection(record_id: str, reason: str, field: str = None):
    """
    Log a rejection during preprocessing.
    Used by T015 to track malformed entries.
    """
    logger = get_logger("preprocessing", logging.WARNING)
    msg = f"Preprocessing rejected record '{record_id}': {reason}"
    if field:
        msg += f" (Field: {field})"
    logger.warning(msg)

def log_preprocessing_rejection_count(total_processed: int, total_rejected: int):
    """Log summary of preprocessing rejections."""
    logger = get_logger("preprocessing", logging.INFO)
    logger.info(
        f"Preprocessing summary: Processed {total_processed}, Rejected {total_rejected}."
    )
