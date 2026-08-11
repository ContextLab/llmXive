import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import get_config

def get_log_path(cycle_number: int) -> str:
    """Get the path for cycle log file."""
    config = get_config()
    log_dir = config.paths.logs_dir
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f"cycle_{cycle_number}.log")

def init_cycle_logger(log_path: str) -> logging.Logger:
    """Initialize a logger for a specific cycle."""
    logger = logging.getLogger(f"cycle_{os.path.basename(log_path)}")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers = []
    
    # File handler
    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.setLevel(logging.INFO)
    
    # JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "message": record.getMessage()
            }
            return json.dumps(log_entry)
    
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    return logger

def update_cycle_log(log_path: str, cycle_number: int, data: Dict[str, Any]) -> None:
    """Update cycle log with new data."""
    log_file = get_log_path(cycle_number)
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, 'a') as f:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "cycle_number": cycle_number,
            **data
        }
        f.write(json.dumps(entry) + "\n")

def checkpoint_model_state(cycle_number: int, state: Dict[str, Any]) -> str:
    """Save model checkpoint."""
    config = get_config()
    checkpoint_dir = config.paths.checkpoints_dir
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    checkpoint_path = os.path.join(checkpoint_dir, f"cycle_{cycle_number}.pt")
    
    with open(checkpoint_path, 'w') as f:
        json.dump(state, f)
    
    return checkpoint_path

def log_cycle_summary(cycle_number: int, metrics: Dict[str, Any]) -> None:
    """Log cycle summary to the cycle log file."""
    log_path = get_log_path(cycle_number)
    logger = init_cycle_logger(log_path)
    
    summary = {
        "cycle_number": cycle_number,
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics
    }
    
    logger.info(json.dumps(summary))

def get_cycle_history(cycle_number: int) -> List[Dict[str, Any]]:
    """Get history of a specific cycle from log file."""
    log_path = get_log_path(cycle_number)
    
    if not os.path.exists(log_path):
        return []
    
    history = []
    with open(log_path, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                history.append(entry)
            except json.JSONDecodeError:
                continue
    
    return history

def log_error(log_path: str, message: str) -> None:
    """Log an error message to the cycle log."""
    logger = init_cycle_logger(log_path)
    logger.error(message)

def log_warning(log_path: str, message: str) -> None:
    """Log a warning message to the cycle log."""
    logger = init_cycle_logger(log_path)
    logger.warning(message)