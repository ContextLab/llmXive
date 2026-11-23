import logging
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO):
    """
    Setup logging infrastructure.
    Creates handlers for console and optionally a file.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = JsonFormatter()
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)

def log_metric(logger: logging.Logger, metric_name: str, value: float, details: Optional[dict] = None):
    """Log a metric value with optional details."""
    msg = f"Metric: {metric_name} = {value}"
    if details:
        msg += f" | Details: {json.dumps(details)}"
    logger.info(msg)

def log_pipeline_event(logger: logging.Logger, event_name: str, status: str, details: Optional[dict] = None):
    """Log a pipeline event."""
    msg = f"Event: {event_name} | Status: {status}"
    if details:
        msg += f" | Details: {json.dumps(details)}"
    logger.info(msg)

def main():
    """Test logging setup."""
    setup_logging()
    logger = get_logger("test")
    logger.info("Logging setup test successful.")

if __name__ == "__main__":
    main()
