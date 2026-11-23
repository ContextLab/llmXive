"""
Logging utilities for the elastic anisotropy pipeline.

Provides structured logging with JSON formatting and convenience functions.
"""
import logging
import json
import sys
from datetime import datetime
from typing import Optional, Any, Dict

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
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
            log_data["extra"] = record.extra_data
        
        return json.dumps(log_data)

def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    use_json: bool = False
) -> logging.Logger:
    """
    Set up a logger with console and optional file handlers.
    
    Args:
        name: Logger name.
        level: Logging level.
        log_file: Optional file path for log output.
        use_json: If True, use JSON formatting.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if use_json:
        console_handler.setFormatter(JsonFormatter())
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        if use_json:
            file_handler.setFormatter(JsonFormatter())
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
    
    return logger

_loggers: Dict[str, logging.Logger] = {}

def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger by name.
    
    Args:
        name: Logger name.
        
    Returns:
        Logger instance.
    """
    if name not in _loggers:
        _loggers[name] = setup_logger(name)
    return _loggers[name]

def log_info(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log an info message."""
    logger.info(message, extra=kwargs)

def log_warning(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log a warning message."""
    logger.warning(message, extra=kwargs)

def log_error(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log an error message."""
    logger.error(message, extra=kwargs)

def log_debug(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log a debug message."""
    logger.debug(message, extra=kwargs)

def log_success(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log a success message (INFO level with success indicator)."""
    logger.info(f"[SUCCESS] {message}", extra=kwargs)

def configure_pipeline_logging(
    log_file: Optional[str] = None,
    use_json: bool = False,
    level: int = logging.INFO
) -> None:
    """
    Configure logging for the entire pipeline.
    
    Args:
        log_file: Optional file path for log output.
        use_json: If True, use JSON formatting.
        level: Logging level.
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if use_json:
        console_handler.setFormatter(JsonFormatter())
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
    
    root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        if use_json:
            file_handler.setFormatter(JsonFormatter())
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
        
        root_logger.addHandler(file_handler)
