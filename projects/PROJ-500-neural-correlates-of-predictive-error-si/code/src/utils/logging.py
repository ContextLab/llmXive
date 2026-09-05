import json
import logging
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data
        return json.dumps(log_data)

class PipelineLogger:
    """Thread-safe logger for pipeline execution."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_dir: Optional[str] = None):
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self.log_dir = Path(log_dir) if log_dir else Path("code/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger("pipeline")
        self.logger.setLevel(logging.INFO)

        # File handler
        log_file = self.log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(console_handler)

    def log_event(self, event: str, data: Optional[Dict[str, Any]] = None):
        """Log an event with optional structured data."""
        record = self.logger.makeRecord(
            self.logger.name, logging.INFO, "", 0, event, (), None
        )
        if data:
            record.extra_data = data
        self.logger.handle(record)

    def log_error(self, error: str, data: Optional[Dict[str, Any]] = None):
        """Log an error with optional structured data."""
        record = self.logger.makeRecord(
            self.logger.name, logging.ERROR, "", 0, error, (), None
        )
        if data:
            record.extra_data = data
        self.logger.handle(record)

    def log_progress(self, stage: str, progress: float, total: float):
        """Log progress update."""
        self.log_event("progress", {"stage": stage, "progress": progress, "total": total})

def get_logger() -> PipelineLogger:
    """Get the singleton pipeline logger instance."""
    return PipelineLogger()

def log_event(event: str, data: Optional[Dict[str, Any]] = None):
    """Convenience function to log an event."""
    return get_logger().log_event(event, data)

def log_error(error: str, data: Optional[Dict[str, Any]] = None):
    """Convenience function to log an error."""
    return get_logger().log_error(error, data)

def log_progress(stage: str, progress: float, total: float):
    """Convenience function to log progress."""
    return get_logger().log_progress(stage, progress, total)
