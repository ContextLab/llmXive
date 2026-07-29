"""
Logging configuration module.
Provides JSON formatting and standard logger setup.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

class JSONFormatter(logging.Formatter):
    """Formatter that outputs logs as JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
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

def setup_logging(log_level: int = logging.INFO, log_file: Optional[Path] = None) -> None:
    """
    Sets up logging for the application.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    root_logger.addHandler(console_handler)
    
    # File Handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Gets a logger with the specified name.
    """
    return logging.getLogger(name)

def log_with_extra(logger: logging.Logger, level: int, message: str, **extra: Any) -> None:
    """
    Logs a message with extra fields (useful for structured logging).
    """
    record = logger.makeRecord(
        logger.name, level, "(unknown file)", 0, message, (), None, extra=extra
    )
    logger.handle(record)

def main():
    """CLI entry point for testing logging."""
    setup_logging(log_file=Path("data/logs/test.log"))
    logger = get_logger(__name__)
    logger.info("Logging system initialized.")
    logger.warning("This is a warning.")
    logger.error("This is an error.")

if __name__ == "__main__":
    main()
