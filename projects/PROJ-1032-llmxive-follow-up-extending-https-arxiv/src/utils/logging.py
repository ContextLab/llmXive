"""Structured JSON logging utilities."""
import json
import logging
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for log records."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        return json.dumps(log_entry)

def setup_json_logger(name: str, output_dir: str = "data/processed/logs"):
    """Setup a JSON logger writing to file."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(output_dir) / f"{name}.log"
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setFormatter(JSONFormatter())
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(JSONFormatter())
    logger.addHandler(ch)
    
    return logger
