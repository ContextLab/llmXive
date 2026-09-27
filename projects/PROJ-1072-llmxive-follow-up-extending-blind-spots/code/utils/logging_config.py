"""
Logging configuration for llmXive pipeline.
Provides structured JSON logging and consistent logger setup.
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional

# Global logger registry to avoid re-configuration
_loggers: Dict[str, logging.Logger] = {}

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)

def setup_root_logger(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    use_json: bool = True
) -> logging.Logger:
    """
    Configure the root logger for the application.
    
    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Path to log file. If None, logs only to console.
        use_json: If True, use JSON formatting.
    
    Returns:
        The configured root logger.
    """
    root_logger = logging.getLogger()
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if use_json:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger, creating it if necessary.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance.
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        # Ensure it doesn't propagate to root if root is already configured
        # but we want to allow propagation for flexibility
        logger.propagate = True
        _loggers[name] = logger
    return _loggers[name]

def log_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    level: int = logging.INFO,
    **kwargs
):
    """
    Log an event with structured data.
    
    Args:
        logger: Logger instance
        event_type: Type of event (e.g., 'start', 'complete', 'error')
        message: Human-readable message
        level: Log level
        **kwargs: Additional data to include in the log
    """
    extra_data = {"event_type": event_type, **kwargs}
    record = logger.makeRecord(
        logger.name, level, "", 0, message, (), None
    )
    record.extra_data = extra_data
    logger.handle(record)
