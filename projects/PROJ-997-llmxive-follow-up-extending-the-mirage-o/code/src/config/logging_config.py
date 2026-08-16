import logging
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import time

# Global logger instance for pipeline progress
_pipeline_logger: Optional[logging.Logger] = None

class JsonLineFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON lines."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": time.time(),
            "sample_id": getattr(record, 'sample_id', None),
            "status": getattr(record, 'status', None),
            "error_code": getattr(record, 'error_code', None),
            "message": record.getMessage(),
            "level": record.levelname
        }
        
        # Include extra fields if present
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)

def ensure_log_dir():
    """Ensure the logs directory exists."""
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def setup_logger(name: str = "pipeline_progress") -> logging.Logger:
    """
    Setup and return a logger configured to write JSON lines to logs/pipeline.log.
    
    Args:
        name: Name of the logger.
        
    Returns:
        Configured logger instance.
    """
    global _pipeline_logger
    
    if _pipeline_logger is not None and _pipeline_logger.name == name:
        return _pipeline_logger
        
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding handlers if they already exist
    if not logger.handlers:
        log_dir = ensure_log_dir()
        log_file_path = log_dir / "pipeline.log"
        
        # Create file handler
        file_handler = logging.FileHandler(log_file_path, mode='a')
        file_handler.setLevel(logging.INFO)
        
        # Set formatter
        formatter = JsonLineFormatter()
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        
        # Prevent propagation to root logger to avoid duplicate console logs if configured elsewhere
        logger.propagate = False
        
        _pipeline_logger = logger
        
    return logger

def log_sample_progress(
    logger: logging.Logger, 
    sample_id: str, 
    status: str, 
    error_code: Optional[str] = None,
    message: Optional[str] = None
):
    """
    Log the progress of a single sample to the pipeline log.
    
    Args:
        logger: The logger instance to use.
        sample_id: Unique identifier for the sample.
        status: Status of the sample processing ('success', 'error', 'skipped').
        error_code: Optional error code if status is 'error' or 'skipped'.
        message: Optional additional message.
    """
    extra_attrs = {
        'sample_id': sample_id,
        'status': status,
        'error_code': error_code
    }
    
    if message:
        extra_attrs['message'] = message
        
    # Create a log record with extra attributes
    # We use a dummy message as the JSON formatter will override it with the structured data
    log_record = logger.makeRecord(
        logger.name, 
        logging.INFO, 
        "", 
        0, 
        f"Sample {sample_id} processed", 
        (), 
        None
    )
    
    # Manually set the extra attributes on the record
    for key, value in extra_attrs.items():
        setattr(log_record, key, value)
        
    logger.handle(log_record)