"""
Logger utilities.
"""
import logging
import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def get_logger(name: str) -> logging.Logger:
    """Get a logger."""
    return logging.getLogger(name)

def init_project_logger(base_path: Path) -> logging.Logger:
    """Initialize project logger."""
    log_dir = base_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline.log"
    
    logger = logging.getLogger("solder_pipeline")
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        fh = logging.FileHandler(str(log_file))
        fh.setFormatter(JSONFormatter())
        logger.addHandler(fh)
        
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(ch)
    
    return logger

def create_module_logger(name: str) -> logging.Logger:
    """Create a module-specific logger."""
    return logging.getLogger(name)

def log(msg: str, level: str = "INFO") -> None:
    """Simple log function."""
    logger = logging.getLogger(__name__)
    getattr(logger, level.lower())(msg)
