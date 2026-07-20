import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, "subject_id"):
            log_record["subject_id"] = record.subject_id
        if hasattr(record, "reason"):
            log_record["reason"] = record.reason
        if hasattr(record, "category"):
            log_record["category"] = record.category
        if hasattr(record, "details"):
            log_record["details"] = record.details

        return json.dumps(log_record)

def setup_logging(log_file: Path, name: str = "pipeline") -> logging.Logger:
    """
    Set up logging to both file and console.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JsonFormatter())
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_provenance(logger: logging.Logger, step: str, details: Dict[str, Any]):
    """
    Log provenance information for a pipeline step.
    """
    logger.info(json.dumps({
        "event": "provenance",
        "step": step,
        "details": details
    }))

def log_exclusion(logger: logging.Logger, subject_id: str, reason: str, category: str, details: Optional[Dict[str, Any]] = None):
    """
    Log an exclusion event for a subject.
    This is the core function for T016: logging excluded subjects and reasons.
    """
    log_data = {
        "event": "exclusion",
        "subject_id": subject_id,
        "reason": reason,
        "category": category,
        "timestamp": datetime.utcnow().isoformat()
    }
    if details:
        log_data["details"] = details
    
    # Log as a structured JSON message
    logger.info(json.dumps(log_data))
    
    # Also log a standard message for readability in the log file
    logger.warning(f"EXCLUDED: Subject {subject_id} - {reason} (Category: {category})")
