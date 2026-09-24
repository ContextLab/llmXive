"""
Base logging infrastructure for the statistical discrepancies research pipeline.
Provides structured logging with JSON formatting and context-aware loggers.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra context if present
        if hasattr(record, 'context'):
            log_data["context"] = record.context
        
        return json.dumps(log_data)


def setup_logging(
    log_file: Optional[Path] = None,
    log_level: int = logging.INFO,
    use_json: bool = False,
    console_output: bool = True
) -> None:
    """
    Configure the root logger with appropriate handlers and formatters.
    
    Args:
        log_file: Optional path to write logs to. If None, logs only to console.
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO).
        use_json: If True, use JSONFormatter; otherwise use standard format.
        console_output: If True, output logs to console.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Formatter selection
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name. If None, uses the module's __name__.
    
    Returns:
        Configured logger instance.
    """
    if name is None:
        # This will be called from a module, so we need to inspect the stack
        # to get the calling module's name. However, for simplicity, we'll
        # return the root logger if no name is provided.
        return logging.getLogger()
    
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a message with additional context data.
    
    Args:
        logger: Logger instance to use.
        level: Logging level.
        message: Log message.
        context: Optional dictionary of context data to include.
    """
    extra = {"context": context} if context else {}
    logger.log(level, message, extra=extra)


def get_logger_for_module(module_name: str) -> logging.Logger:
    """
    Get a logger configured for a specific module.
    
    Args:
        module_name: The name of the module (typically __name__).
    
    Returns:
        Logger instance named after the module.
    """
    return logging.getLogger(module_name)
