import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

MEMORY_LOG_PATH = "data/processed/memory_log.json"
logger = logging.getLogger(__name__)

def initialize_memory_log() -> None:
    """Initialize the memory log file with a timestamp entry."""
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        "initialized_at": datetime.now().isoformat(),
        "events": []
    }
    
    with open(MEMORY_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, indent=2)
    
    logger.info(f"Memory log initialized at {MEMORY_LOG_PATH}")

def log_memory_usage(usage_gb: float, batch_size: int) -> None:
    """Log memory usage and batch size."""
    try:
        with open(MEMORY_LOG_PATH, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log_data = {"events": []}
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": "memory_usage",
        "usage_gb": usage_gb,
        "batch_size": batch_size
    }
    
    log_data["events"].append(event)
    
    with open(MEMORY_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

def log_timeout_error(task_id: str, style: str, timeout_seconds: int) -> None:
    """Log a timeout error for a specific task."""
    try:
        with open(MEMORY_LOG_PATH, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log_data = {"events": []}
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": "timeout_error",
        "task_id": task_id,
        "style": style,
        "timeout_seconds": timeout_seconds
    }
    
    log_data["events"].append(event)
    
    with open(MEMORY_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    
    logger.error(f"Timeout error: Task {task_id} ({style}) exceeded {timeout_seconds}s")

def log_generation_error(task_id: str, style: str, error_msg: str) -> None:
    """Log a generation error."""
    try:
        with open(MEMORY_LOG_PATH, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log_data = {"events": []}
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": "generation_error",
        "task_id": task_id,
        "style": style,
        "error": error_msg
    }
    
    log_data["events"].append(event)
    
    with open(MEMORY_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    
    logger.error(f"Generation error: Task {task_id} ({style}) - {error_msg}")

def log_batch_reduction(old_batch: int, new_batch: int, reason: str) -> None:
    """Log a batch size reduction."""
    try:
        with open(MEMORY_LOG_PATH, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log_data = {"events": []}
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": "batch_reduction",
        "old_batch_size": old_batch,
        "new_batch_size": new_batch,
        "reason": reason
    }
    
    log_data["events"].append(event)
    
    with open(MEMORY_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Batch size reduced: {old_batch} -> {new_batch} ({reason})")

def get_memory_log_path() -> str:
    """Return the path to the memory log file."""
    return MEMORY_LOG_PATH

def get_memory_log() -> Dict[str, Any]:
    """Load and return the entire memory log."""
    try:
        with open(MEMORY_LOG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"events": []}
