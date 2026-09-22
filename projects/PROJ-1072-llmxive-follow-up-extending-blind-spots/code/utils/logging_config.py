import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Optional

_root_logger: Optional[logging.Logger] = None

class JsonFormatter(logging.Formatter):
    """Custom formatter to output logs as JSON lines."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_entry["exc_info"] = self.format_exception(record.exc_info)
        return json.dumps(log_entry)

def setup_root_logger(name: str = "blind_spots_pipeline", log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Initialize the root logger for the pipeline.
    
    Args:
        name: Logger name.
        log_file: Optional path to a log file.
        level: Logging level.
        
    Returns:
        Configured logger instance.
    """
    global _root_logger
    if _root_logger:
        return _root_logger

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setLevel(level)
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)
    
    _root_logger = logger
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger of the root.
    
    Args:
        name: Logger name (e.g., module name).
        
    Returns:
        Logger instance.
    """
    if not _root_logger:
        setup_root_logger()
    return logging.getLogger(name)

def log_event(logger: logging.Logger, event_type: str, message: str, **kwargs):
    """
    Log a structured event.
    
    Args:
        logger: Logger instance.
        event_type: Type of event (e.g., 'INFO', 'ERROR').
        message: Event message.
        **kwargs: Additional context data.
    """
    extra_context = json.dumps(kwargs)
    full_message = f"{message} | Context: {extra_context}"
    logger.info(full_message)
