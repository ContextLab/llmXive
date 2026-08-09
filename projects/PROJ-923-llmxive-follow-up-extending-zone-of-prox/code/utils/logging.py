"""
Logging infrastructure.
Configures logging to stdout and file with JSON formatting.
"""
import logging
import os
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName
        }
        if hasattr(record, 'metric_name'):
            log_obj["metric_name"] = record.metric_name
            log_obj["metric_value"] = record.metric_value
        return json.dumps(log_obj)

def configure_logging(log_file: Optional[str] = None, level: int = logging.INFO):
    """Configures the root logger."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(JsonFormatter())
    root_logger.addHandler(ch)
    
    # File handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(JsonFormatter())
        root_logger.addHandler(fh)

def get_logger(name: str) -> logging.Logger:
    """Gets a logger with the given name."""
    return logging.getLogger(name)

def log_metric(name: str, value: float, step: Optional[int] = None):
    """Logs a metric to the logger."""
    logger = get_logger("metrics")
    record = logger.makeRecord(
        logger.name, logging.INFO, "", 0, "", (), None
    )
    record.metric_name = name
    record.metric_value = value
    record.step = step
    logger.handle(record)

def log_run_metadata(metadata: Dict[str, Any]):
    """Logs run metadata."""
    logger = get_logger("metadata")
    logger.info(json.dumps(metadata))
