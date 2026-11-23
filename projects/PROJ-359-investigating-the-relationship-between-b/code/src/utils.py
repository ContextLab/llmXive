"""
Utility functions for the llmXive automated science pipeline.

Provides:
- Deterministic seeding based on RANDOM_SEED environment variable
- JSON logging infrastructure for pipeline events and metrics
- Path management for logs
"""
import json
import os
import random
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

# Constants
RANDOM_SEED = int(os.environ.get("RANDOM_SEED", 42))
MOTION_THRESHOLD_MM = 3.0  # FR-002 mandated threshold

# Project root relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOG_DIR = _PROJECT_ROOT / "data" / "logs"

def seed_manager(seed: Optional[int] = None) -> None:
    """
    Initialize deterministic seeding for the entire pipeline.

    Args:
        seed: Optional seed override. If None, uses RANDOM_SEED env var.
    """
    if seed is None:
        seed = RANDOM_SEED

    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    
    # Seed numpy if available (lazy import to avoid hard dependency in utils)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def get_log_path(filename: str = "pipeline_log.json") -> Path:
    """
    Get the absolute path for a log file in the data/logs directory.
    
    Args:
        filename: Name of the log file.
        
    Returns:
        Path to the log file.
    """
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    return _LOG_DIR / filename

def load_existing_log(filename: str = "pipeline_log.json") -> Dict[str, Any]:
    """
    Load an existing JSON log file or return a fresh structure.
    
    Args:
        filename: Name of the log file.
        
    Returns:
        Dictionary containing log data.
    """
    log_path = get_log_path(filename)
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "pipeline_status": "initialized",
        "start_time": datetime.now().isoformat(),
        "events": [],
        "metrics": {},
        "exclusion_motion": 0,
        "exclusion_missing_wm": 0,
        "exclusion_missing_id": 0,
        "total_runtime_seconds": 0.0
    }

def write_json_log(data: Dict[str, Any], filename: str = "pipeline_log.json") -> None:
    """
    Write data to a JSON log file atomically.
    
    Args:
        data: Dictionary to write.
        filename: Name of the log file.
    """
    log_path = get_log_path(filename)
    temp_path = log_path.with_suffix(".tmp")
    
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    
    temp_path.replace(log_path)

def log_event(
    event_type: str, 
    message: str, 
    data: Optional[Dict[str, Any]] = None,
    filename: str = "pipeline_log.json"
) -> None:
    """
    Log an event to the JSON log file.
    
    Args:
        event_type: Type of event (e.g., 'INFO', 'ERROR', 'WARNING').
        message: Human-readable message.
        data: Optional structured data associated with the event.
        filename: Name of the log file.
    """
    log_data = load_existing_log(filename)
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "message": message,
        "data": data or {}
    }
    
    log_data["events"].append(event)
    write_json_log(log_data, filename)

def log_json_metric(
    metric_name: str, 
    value: Any, 
    filename: str = "pipeline_log.json"
) -> None:
    """
    Log a metric to the JSON log file.
    
    Args:
        metric_name: Name of the metric.
        value: Value of the metric.
        filename: Name of the log file.
    """
    log_data = load_existing_log(filename)
    log_data["metrics"][metric_name] = value
    write_json_log(log_data, filename)

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = "pipeline_debug.log"
) -> logging.Logger:
    """
    Setup the standard Python logging infrastructure.
    
    Args:
        log_level: Logging level (e.g., logging.INFO).
        log_file: Optional filename for file logging.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler (optional)
    if log_file:
        log_path = get_log_path(log_file)
        fh = logging.FileHandler(log_path)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

def get_pipeline_status(filename: str = "pipeline_log.json") -> str:
    """
    Retrieve the current pipeline status from the log.
    
    Args:
        filename: Name of the log file.
        
    Returns:
        Current status string.
    """
    log_data = load_existing_log(filename)
    return log_data.get("pipeline_status", "unknown")

def update_pipeline_status(
    status: str, 
    filename: str = "pipeline_log.json"
) -> None:
    """
    Update the pipeline status in the log.
    
    Args:
        status: New status string.
        filename: Name of the log file.
    """
    log_data = load_existing_log(filename)
    log_data["pipeline_status"] = status
    
    # Update end time if finished
    if status == "SUCCESS":
        log_data["end_time"] = datetime.now().isoformat()
        log_data["total_runtime_seconds"] = (
            datetime.fromisoformat(log_data["end_time"]).timestamp() -
            datetime.fromisoformat(log_data["start_time"]).timestamp()
        )
    
    write_json_log(log_data, filename)