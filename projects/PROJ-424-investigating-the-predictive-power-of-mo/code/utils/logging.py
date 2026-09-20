"""
Logging utilities for structured logging.
"""
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a logger with JSON formatting and optional file output.
    
    Args:
        name: Logger name.
        log_file: Optional filename for log output.
        level: Logging level.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = LOG_DIR / log_file
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get an existing logger or create one if it doesn't exist."""
    return logging.getLogger(name)

def log_event(logger: logging.Logger, event: str, data: Optional[Dict[str, Any]] = None):
    """Log a structured event."""
    message = event
    if data:
        message += f" | Data: {json.dumps(data)}"
    logger.info(message)

def log_sensitivity_results(logger: logging.Logger, solvent: str, results: Dict[str, Any]):
    """Log sensitivity analysis results."""
    logger.info(f"Sensitivity results for {solvent}: {json.dumps(results)}")

def main():
    """Test the logging setup."""
    logger = setup_logger("test_logger", "test.log")
    logger.info("Test log message")
    logger.warning("Test warning")
    logger.error("Test error")

if __name__ == "__main__":
    main()