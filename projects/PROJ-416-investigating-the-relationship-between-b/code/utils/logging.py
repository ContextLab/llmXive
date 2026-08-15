import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

class JsonFormatter(logging.Formatter):
    """Custom formatter for JSON structured logging."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        return json.dumps(log_entry)

def setup_logging(config):
    """Configure logging for the pipeline."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_file = config.LOGS_DIR / "pipeline.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

def log_provenance(logger: logging.Logger, stage: str, details: Dict[str, Any]):
    """Log provenance information for a pipeline stage."""
    extra = {"stage": stage, **details}
    record = logger.makeRecord(
        logger.name, logging.INFO, "", 0,
        f"Provenance: {stage}", (), None
    )
    record.extra_data = extra
    logger.handle(record)

def log_exclusion(logger: logging.Logger, subject_id: str, reason: str):
    """Log subject exclusion with reason."""
    logger.info(f"Excluding subject {subject_id}: {reason}", extra={"subject_id": subject_id, "reason": reason})