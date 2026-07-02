"""
Logging utilities for the Brain Network Dynamics pipeline.
Provides structured logging and provenance tracking.
"""
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs JSON logs."""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logging(level: int = logging.INFO, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Configure root logger with console and optional file handlers.
    
    Args:
        level: Logging level (e.g., logging.INFO).
        log_file: Optional path to write logs to.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("pipeline")
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)
        
    return logger

def log_provenance(logger: logging.Logger, stage: str, details: Dict[str, Any]) -> None:
    """Log structured provenance information for a pipeline stage."""
    extra_data = {
        "provenance_stage": stage,
        "timestamp": datetime.utcnow().isoformat(),
        **details
    }
    logger.info("Provenance", extra={"json": extra_data})
    
def log_exclusion(logger: logging.Logger, subject_id: str, reason: str) -> None:
    """Log subject exclusion with reason."""
    logger.warning(f"Subject excluded: {subject_id} | Reason: {reason}")
