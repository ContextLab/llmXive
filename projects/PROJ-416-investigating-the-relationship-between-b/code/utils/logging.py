"""
Logging utilities for the pipeline.
"""
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
            "function": record.funcName
        }
        return json.dumps(log_obj)

def setup_logging(log_file: Optional[Path] = None, console: bool = True):
    """
    Setup logging configuration.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JsonFormatter())
        root_logger.addHandler(file_handler)
    
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        root_logger.addHandler(console_handler)

def log_provenance(stage: str, details: Dict[str, Any]):
    """
    Log provenance information for a stage.
    """
    logging.info(f"Provenance: {stage} - {json.dumps(details)}")

def log_exclusion(subject_id: str, reason: str):
    """
    Log subject exclusion.
    """
    logging.info(f"Exclusion: Subject {subject_id} - {reason}")
