import logging
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from config import get_project_root, get_log_dir
from typing import Optional

class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON logs."""
    
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def get_json_formatter() -> JSONFormatter:
    """
    Get the JSON formatter instance.
    
    Returns:
        JSONFormatter instance
    """
    return JSONFormatter()

def setup_logging(
    level: int = logging.INFO, 
    log_file: Optional[Path] = None
) -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level
        log_file: Optional path to log file
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(get_json_formatter())
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(get_json_formatter())
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def main():
    """Main entry point for logging config (for testing)."""
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Logging configuration test")
