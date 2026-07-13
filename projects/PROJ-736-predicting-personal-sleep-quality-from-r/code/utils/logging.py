"""
Logging module for structured JSON logging.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_paths, ensure_dirs

class JSONFormatter(logging.Formatter):
    """
    Custom formatter for JSON logging.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        return json.dumps(log_data)

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_file: Path to log file (optional)
        
    Returns:
        Configured logger
    """
    ensure_dirs()
    
    # Create logger
    logger = logging.getLogger('pipeline')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file provided)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger

def log_event(logger: logging.Logger, event: str, data: Optional[Dict[str, Any]] = None):
    """
    Log an event with optional data.
    
    Args:
        logger: Logger instance
        event: Event name
        data: Optional data dictionary
    """
    extra = {'extra_data': data} if data else {}
    logger.info(json.dumps({'event': event, **data}), extra=extra)

def log_stage_start(logger: logging.Logger, stage: str):
    """
    Log the start of a pipeline stage.
    
    Args:
        logger: Logger instance
        stage: Stage name
    """
    logger.info(f"--- Starting stage: {stage} ---")

def log_stage_complete(logger: logging.Logger, stage: str, extra: Optional[Dict[str, Any]] = None):
    """
    Log the completion of a pipeline stage.
    
    Args:
        logger: Logger instance
        stage: Stage name
        extra: Optional extra data
    """
    msg = f"--- Completed stage: {stage} ---"
    if extra:
        msg += f" ({json.dumps(extra)})"
    logger.info(msg)

def log_stage_error(logger: logging.Logger, stage: str, error: str):
    """
    Log an error during a pipeline stage.
    
    Args:
        logger: Logger instance
        stage: Stage name
        error: Error message
    """
    logger.error(f"--- Error in stage: {stage} --- {error}")
