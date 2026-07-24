import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, Union
import os

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info:
            log_obj["exc_info"] = traceback.format_exception(*record.exc_info)
        
        if hasattr(record, 'extra_data'):
            log_obj.update(record.extra_data)
            
        return json.dumps(log_obj)

class TextFormatter(logging.Formatter):
    """Custom formatter for human-readable text logging."""
    
    def format(self, record):
        return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {record.levelname}: {record.getMessage()}"

def get_logger(name: str, level: int = logging.INFO, use_json: bool = False) -> logging.Logger:
    """
    Retrieves or creates a logger with the specified name.
    
    Args:
        name: The name of the logger.
        level: The logging level.
        use_json: If True, use StructuredFormatter; otherwise, TextFormatter.
        
    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        if use_json:
            formatter = StructuredFormatter()
        else:
            formatter = TextFormatter()
            
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

def log_event(logger: logging.Logger, event_type: str, message: str, data: Optional[Dict[str, Any]] = None):
    """
    Logs a specific event with optional extra data.
    
    Args:
        logger: The logger instance.
        event_type: The type of event (e.g., 'START', 'ERROR').
        message: The log message.
        data: Optional dictionary of extra data to include.
    """
    if data:
        record = logger.makeRecord(logger.name, logging.INFO, "", 0, message, (), None)
        record.extra_data = {"event_type": event_type, **data}
        logger.handle(record)
    else:
        logger.info(f"[{event_type}] {message}")

def setup_pipeline_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger specifically for pipeline operations.
    
    Args:
        name: The name of the logger.
        level: The logging level.
        
    Returns:
        A configured logger instance.
    """
    return get_logger(name, level, use_json=False)
