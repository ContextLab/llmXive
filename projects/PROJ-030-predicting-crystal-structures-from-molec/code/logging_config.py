"""
Logging configuration for the pipeline.
Provides structured JSON logging and standard console output.
"""
import logging
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON logs."""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logging(log_level: str = "INFO", log_dir: Optional[str] = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_dir: Directory to store log files. If None, logs to console only.
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers = []

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File Handler (JSON)
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance by name."""
    return logging.getLogger(name)

def log_event(logger: logging.Logger, level: str, message: str, **kwargs):
    """Log an event with additional context."""
    extra_msg = f" | Context: {kwargs}" if kwargs else ""
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"{message}{extra_msg}")

def main():
    """Test logging setup."""
    setup_logging(log_level="DEBUG", log_dir="logs")
    logger = get_logger("test")
    logger.info("Logging system initialized.")

if __name__ == "__main__":
    main()
