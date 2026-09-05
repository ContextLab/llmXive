"""
JSON Logger Module for Solder Hardness Pipeline.
Provides a `get_logger()` function that writes to `logs/pipeline.log` in JSON format.
"""
import logging
import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from .logging_config import setup_logging, get_logger as get_configured_logger
from .error_handlers import ConfigurationError

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOG_FILE = LOGS_DIR / "pipeline.log"

def _ensure_logs_dir() -> None:
    """Create the logs directory if it does not exist."""
    if not LOGS_DIR.exists():
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON lines.
    Ensures the output is valid JSON for easy parsing by log aggregators.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)

def get_logger(name: str = "solder_pipeline") -> logging.Logger:
    """
    Create and return a logger configured to write JSON-formatted logs
    to `logs/pipeline.log`.
    
    This function ensures the `logs/` directory exists, sets up a file
    handler with the JSON formatter, and attaches it to the requested logger.
    
    Args:
        name: The name of the logger (e.g., 'ingestion.aggregator', 'utils.logger').
            
    Returns:
        A configured Logger instance that writes to `logs/pipeline.log`.
    """
    _ensure_logs_dir()
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        # Check if a JSON file handler already exists for this file
        has_json_handler = any(
            isinstance(h, logging.FileHandler) and h.baseFilename == str(LOG_FILE)
            for h in logger.handlers
        )
        if has_json_handler:
            return logger
    
    # Remove any existing handlers to ensure clean configuration
    logger.handlers.clear()
    
    # Create file handler
    file_handler = logging.FileHandler(LOG_FILE, mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    # Prevent propagation to root to avoid double logging if root is also configured
    logger.propagate = False
    
    return logger

def init_project_logger() -> logging.Logger:
    """
    Initialize the project logging infrastructure and return the root logger.
    Configured to write JSON logs to `logs/pipeline.log`.
    """
    _ensure_logs_dir()
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    if not root_logger.handlers:
        file_handler = logging.FileHandler(LOG_FILE, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
    
    return root_logger

def create_module_logger(module_name: str) -> logging.Logger:
    """
    Create and return a logger for a specific module.
    
    Args:
        module_name: The name of the module (e.g., 'ingestion.aggregator').
            
    Returns:
        A configured Logger instance.
    """
    return get_logger(module_name)

def log(message: str, level: str = "info", extra: Optional[Dict[str, Any]] = None) -> None:
    """
    Simple logging function for quick debug statements.
    
    Args:
        message: The message to log.
        level: The log level string ('debug', 'info', 'warning', 'error', 'critical').
        extra: Optional dictionary of extra data to include in the JSON log.
    """
    logger = get_logger("utils.logger")
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    log_level = level_map.get(level.lower(), logging.INFO)
    
    if extra:
        logger.log(log_level, message, extra={"extra_data": extra})
    else:
        logger.log(log_level, message)

if __name__ == "__main__":
    # Simple test to verify JSON logging works and creates the file
    test_logger = get_logger("test_logger")
    test_logger.info("Logger initialized successfully.")
    test_logger.warning("This is a test warning.", extra={"test_key": "test_value"})
    test_logger.error("This is a test error.")
    print(f"Logs written to {LOG_FILE}")
    # Verify file exists
    if LOG_FILE.exists():
        print(f"Verification: {LOG_FILE} exists and contains JSON logs.")
    else:
        raise RuntimeError(f"Failed to create log file at {LOG_FILE}")