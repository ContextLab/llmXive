"""
Logger utilities for the solder hardness prediction pipeline.

Provides a JSON-formatted logger that writes to logs/pipeline.log.
"""
import logging
import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

class JSONFormatter(logging.Formatter):
    """Format log records as JSON lines."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "name": record.name,
            "level": record.levelname,
            "levelno": record.levelno,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, 'exc_text') and record.exc_text:
            log_data["exception_text"] = record.exc_text
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data
            
        return json.dumps(log_data)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: The name of the logger (typically __name__ of the module)
            
    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)

def init_project_logger(base_path: Path, log_level: int = logging.DEBUG) -> logging.Logger:
    """
    Initialize the project-wide logger that writes to logs/pipeline.log in JSON format.
    
    Args:
        base_path: The root path of the project
        log_level: The logging level to use (default: DEBUG)
            
    Returns:
        The configured project logger
            
    Raises:
        FileNotFoundError: If the logs directory cannot be created
    """
    log_dir = base_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline.log"
    
    logger = logging.getLogger("solder_pipeline")
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # File handler for JSON logs
    fh = logging.FileHandler(str(log_file))
    fh.setLevel(log_level)
    fh.setFormatter(JSONFormatter())
    logger.addHandler(fh)
    
    # Console handler for human-readable logs
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    ch.setFormatter(console_formatter)
    logger.addHandler(ch)
    
    return logger

def create_module_logger(name: str, base_path: Optional[Path] = None) -> logging.Logger:
    """
    Create a module-specific logger.
    
    If base_path is provided, initializes the project logger first to ensure
    the log file exists and handlers are set up.
    
    Args:
        name: The name of the logger (typically __name__)
        base_path: Optional project root path to initialize project logger
            
    Returns:
        A logger instance for the module
    """
    if base_path is not None:
        init_project_logger(base_path)
    
    return logging.getLogger(name)

def log(msg: str, level: str = "INFO", name: Optional[str] = None) -> None:
    """
    Simple logging function for quick logging without explicit logger creation.
    
    Args:
        msg: The message to log
        level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        name: Optional logger name (defaults to __name__)
    """
    logger = logging.getLogger(name if name else __name__)
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(msg)

def log_with_extra(msg: str, extra_data: Dict[str, Any], level: str = "INFO", name: Optional[str] = None) -> None:
    """
    Log a message with additional structured data included in the JSON output.
    
    Args:
        msg: The message to log
        extra_data: Dictionary of additional data to include in the log record
        level: The logging level
        name: Optional logger name
    """
    logger = logging.getLogger(name if name else __name__)
    
    # Create a custom log record with extra data
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper(), logging.INFO),
        "",
        0,
        msg,
        (),
        None
    )
    record.extra_data = extra_data
    
    logger.handle(record)