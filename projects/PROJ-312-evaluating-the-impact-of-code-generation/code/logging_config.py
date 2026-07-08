import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "pipeline.log"

def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # File handler with JSON formatting
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
    file_handler.setLevel(logging.INFO)
    
    # Custom formatter to output JSON
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName
            }
            if hasattr(record, 'extra_data'):
                log_record.update(record.extra_data)
            return json.dumps(log_record)

    file_handler.setFormatter(JsonFormatter())
    
    if not logger.handlers:
        logger.addHandler(file_handler)
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def capture_rate_limit_headers(headers: Dict[str, Any]):
    """
    Captures GitHub rate limit headers and logs them.
    """
    remaining = headers.get("X-RateLimit-Remaining")
    reset = headers.get("X-RateLimit-Reset")
    
    if remaining is not None:
        logger = get_logger(__name__)
        logger.info(f"Rate limit remaining: {remaining}, reset at: {reset}", extra={"extra_data": {"rate_limit_remaining": remaining, "rate_limit_reset": reset}})
