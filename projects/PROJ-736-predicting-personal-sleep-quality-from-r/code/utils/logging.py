import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from config import get_paths, ensure_dirs

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logging():
    """Setup logging to both console and file."""
    paths = get_paths()
    ensure_dirs()
    
    log_file = paths['log_file']
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers = []
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    fh.setFormatter(JSONFormatter())
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def log_event(event_type, message, **kwargs):
    """Log a structured event."""
    logger = logging.getLogger()
    event_data = {
        "event_type": event_type,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        **kwargs
    }
    logger.info(json.dumps(event_data))

def log_stage_start(stage_name, description):
    """Log the start of a pipeline stage."""
    logger = logging.getLogger()
    logger.info(f"[STAGE_START] {stage_name}: {description}")

def log_stage_complete(stage_name, description):
    """Log the completion of a pipeline stage."""
    logger = logging.getLogger()
    logger.info(f"[STAGE_COMPLETE] {stage_name}: {description}")

def log_stage_error(stage_name, error_message):
    """Log an error in a pipeline stage."""
    logger = logging.getLogger()
    logger.error(f"[STAGE_ERROR] {stage_name}: {error_message}")
