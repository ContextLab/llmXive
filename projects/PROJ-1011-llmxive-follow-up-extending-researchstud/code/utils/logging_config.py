import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union, List, TYPE_CHECKING
import json
from datetime import datetime

# Fix for missing Dict import in type hints
if TYPE_CHECKING:
    from typing import Dict

def ensure_log_dir(log_dir: Optional[Path] = None) -> Path:
    """Ensure the logging directory exists."""
    if log_dir is None:
        log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

class PIIFilter(logging.Filter):
    """Filter to remove PII from logs."""
    def filter(self, record: logging.LogRecord) -> bool:
        # Basic PII filtering logic
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            if 'email' in record.msg.lower() or 'phone' in record.msg.lower():
                record.msg = record.msg.replace('email', '[EMAIL]').replace('phone', '[PHONE]')
        return True

def get_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Get a logger with optional file handler."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(PIIFilter())
    logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        ensure_log_dir(log_path.parent)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(PIIFilter())
        logger.addHandler(file_handler)

    return logger

def get_model_fallback_logger() -> logging.Logger:
    """Get a logger specifically for model fallback events."""
    return get_logger("model_fallback", "logs/model_fallback.log")

def log_model_switch(logger: logging.Logger, old_model: str, new_model: str, reason: str) -> None:
    """Log a model switch event."""
    logger.info(f"Switching model from {old_model} to {new_model}. Reason: {reason}")

def log_memory_error(logger: logging.Logger, memory_usage_gb: float, threshold_gb: float) -> None:
    """Log a memory error event."""
    logger.error(f"Memory usage {memory_usage_gb:.2f}GB exceeded threshold {threshold_gb:.2f}GB.")

def log_fallback_success(logger: logging.Logger, model_name: str) -> None:
    """Log successful fallback to a smaller model."""
    logger.info(f"Successfully loaded fallback model: {model_name}")

def log_fallback_failure(logger: logging.Logger, error_msg: str) -> None:
    """Log failure to load fallback model."""
    logger.error(f"Fallback model loading failed: {error_msg}")

def log_acquisition_failure(logger: logging.Logger, source: str, error: str) -> None:
    """Log data acquisition failure."""
    logger.error(f"Acquisition failed for {source}: {error}")

def log_preprocessing_rejection(logger: logging.Logger, record_id: str, reason: str) -> None:
    """Log a record rejected during preprocessing."""
    logger.warning(f"Record {record_id} rejected: {reason}")

def log_preprocessing_rejection_count(logger: logging.Logger, count: int) -> None:
    """Log the total count of rejected records."""
    logger.info(f"Total records rejected during preprocessing: {count}")

def sanitize_structured_log(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize structured log data to remove PII."""
    if not isinstance(data, dict):
        return data
    
    sanitized = {}
    pii_keys = ['email', 'phone', 'ssn', 'credit_card', 'password']
    
    for key, value in data.items():
        if key.lower() in pii_keys:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_structured_log(value)
        else:
            sanitized[key] = value
    
    return sanitized

def initialize_pipeline_logging(log_dir: Optional[Path] = None) -> None:
    """Initialize logging for the entire pipeline."""
    log_path = log_dir or Path("logs")
    ensure_log_dir(log_path)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    if not root_logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(PIIFilter())
        root_logger.addHandler(console_handler)
        
        file_handler = logging.FileHandler(log_path / "pipeline.log")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(PIIFilter())
        root_logger.addHandler(file_handler)

def log_data_source_check(logger: logging.Logger, source_name: str, status: str, details: Optional[str] = None) -> None:
    """Log the result of a data source health check."""
    msg = f"Data source check for {source_name}: {status}"
    if details:
        msg += f" - {details}"
    
    if status == "OK":
        logger.info(msg)
    else:
        logger.error(msg)
