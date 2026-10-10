"""
Structured logger for the llmXive pipeline.
Produces JSON lines for machine-readability and tracks pipeline statistics.
"""
import logging
import json
import sys
from pathlib import Path
from typing import Any

class JsonFormatter(logging.Formatter):
    """Custom formatter to output logs as JSON lines."""
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

# Global statistics counters
_stats = {"processed": 0, "skipped": 0}

def setup_pipeline_logging():
    """
    Configures the root logger to output JSON lines to both a file 
    and the console.
    """
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline.log"

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # JSON File Handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(file_handler)

    # Console Handler (Human readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

def increment_pr_processed(n: int = 1):
    """Increment the global count of processed pull requests."""
    _stats["processed"] += n

def increment_pr_skipped(n: int = 1):
    """Increment the global count of skipped pull requests."""
    _stats["skipped"] += n

def get_logger(name: str) -> logging.Logger:
    """Return a logger instance for the given name."""
    return logging.getLogger(name)
