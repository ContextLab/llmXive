"""
T008: Logging configuration for the pipeline.
Configures a FileHandler to logs/pipeline.log with JSON formatting.
"""
import logging
import json
import os
from pathlib import Path
from typing import Any

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
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

def configure_logging(log_file: str = "logs/pipeline.log", level: int = logging.INFO) -> None:
    """
    Configure logging with a FileHandler to the specified log file.
    
    Args:
        log_file: Path to the log file
        level: Logging level (default: INFO)
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # File handler with JSON formatting
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(JSONFormatter())

    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.info(f"Logging configured: file={log_file}, level={logging.getLevelName(level)}")

if __name__ == "__main__":
    configure_logging()
    logging.info("Test log message")
