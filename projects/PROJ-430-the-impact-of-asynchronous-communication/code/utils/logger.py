import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        if hasattr(record, 'extra_data'):
            log_obj.update(record.extra_data)
        return json.dumps(log_obj)

def setup_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(JSONFormatter())
            logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    return setup_logger(name)

def log_event(logger: logging.Logger, event_type: str, data: Dict[str, Any]):
    extra = {'extra_data': {'event_type': event_type, **data}}
    logger.info(f"Event: {event_type}", extra=extra)

def log_pipeline_start(logger: logging.Logger, project_id: str):
    log_event(logger, "pipeline_start", {"project_id": project_id})

def log_pipeline_complete(logger: logging.Logger, project_id: str):
    log_event(logger, "pipeline_complete", {"project_id": project_id})

def log_pipeline_error(logger: logging.Logger, project_id: str, error: str):
    log_event(logger, "pipeline_error", {"project_id": project_id, "error": error})