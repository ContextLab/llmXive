import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logging(log_file: Path, level: str = "INFO") -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_file: Path to log file
        level: Logging level
        
    Returns:
        Root logger
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers = []
    
    # File handler
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    return logger

def log_provenance(step: str, details: Dict[str, Any]) -> None:
    """
    Log provenance information for a pipeline step.
    
    Args:
        step: Step name
        details: Step details
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Provenance: {step} - {json.dumps(details)}")

def log_exclusion(subject_id: str, reason: str) -> None:
    """
    Log subject exclusion.
    
    Args:
        subject_id: Subject ID
        reason: Exclusion reason
    """
    logger = logging.getLogger(__name__)
    logger.warning(f"Excluded subject {subject_id}: {reason}")
