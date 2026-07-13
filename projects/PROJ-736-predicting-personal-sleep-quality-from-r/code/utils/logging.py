import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from config import get_paths

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
    """Setup logging to console and file."""
    paths = get_paths()
    log_file = paths['logs'] / 'pipeline_run.json'
    os.makedirs(str(paths['logs']), exist_ok=True)

    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers = []

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler(str(log_file))
    fh.setFormatter(JSONFormatter())
    logger.addHandler(fh)

    return logger

def log_stage_start(stage: str, message: str):
    logger = logging.getLogger("llmXive")
    logger.info(f"[{stage}] START: {message}")

def log_stage_complete(stage: str, message: str):
    logger = logging.getLogger("llmXive")
    logger.info(f"[{stage}] COMPLETE: {message}")

def log_stage_error(stage: str, message: str):
    logger = logging.getLogger("llmXive")
    logger.error(f"[{stage}] ERROR: {message}")

def log_event(event: str, details: dict):
    logger = logging.getLogger("llmXive")
    logger.info(json.dumps({"event": event, **details}))
