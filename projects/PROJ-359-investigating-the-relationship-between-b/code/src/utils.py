"""
Utility functions for the llmXive science pipeline.

Provides:
- Deterministic seeding via RANDOM_SEED environment variable
- JSON logging infrastructure for pipeline events and metrics
- Path utilities for log file management
"""
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
import logging
import sys

# Project root path (assumed to be parent of 'code' directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "data" / "logs"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Constants
MOTION_THRESHOLD_MM = 3.0  # FR-002: Motion exclusion threshold

# Global logger instance
_logger = None
_log_file_path = None


def seed_manager(seed_env_var: str = "RANDOM_SEED") -> int:
    """
    Initialize deterministic seeding for the entire pipeline.
    
    Reads the RANDOM_SEED environment variable. If not set, defaults to 42.
    Seeds python.random, numpy (if available), and sets the environment variable.
    
    Args:
        seed_env_var: Name of the environment variable to read the seed from.
        
    Returns:
        The integer seed value used.
    """
    seed_str = os.environ.get(seed_env_var, "42")
    try:
        seed_value = int(seed_str)
    except ValueError:
        seed_value = 42
        os.environ[seed_env_var] = "42"
    
    random.seed(seed_value)
    
    # Seed numpy if available
    try:
        import numpy as np
        np.random.seed(seed_value)
    except ImportError:
        pass
    
    # Seed torch if available (for future compatibility)
    try:
        import torch
        torch.manual_seed(seed_value)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed_value)
    except ImportError:
        pass
    
    os.environ[seed_env_var] = str(seed_value)
    return seed_value


def get_log_path(filename: str = "pipeline_log.json") -> Path:
    """
    Get the full path for a log file.
    
    Args:
        filename: Name of the log file (default: pipeline_log.json).
        
    Returns:
        Path object pointing to the log file.
    """
    return LOG_DIR / filename


def load_existing_log(filename: str = "pipeline_log.json") -> dict:
    """
    Load an existing JSON log file.
    
    Args:
        filename: Name of the log file.
        
    Returns:
        Dictionary containing the log data, or empty dict if file doesn't exist.
    """
    log_path = get_log_path(filename)
    if log_path.exists():
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"events": []}
    return {"events": []}


def write_json_log(data: dict, filename: str = "pipeline_log.json") -> Path:
    """
    Write data to a JSON log file.
    
    Args:
        data: Dictionary to write as JSON.
        filename: Name of the log file.
        
    Returns:
        Path to the written file.
    """
    log_path = get_log_path(filename)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    return log_path


def log_event(
    event_type: str,
    message: str,
    data: dict = None,
    filename: str = "pipeline_log.json",
    level: str = "INFO"
) -> dict:
    """
    Log an event to the JSON log file.
    
    Args:
        event_type: Type/category of the event (e.g., "START", "ERROR", "METRIC").
        message: Human-readable description of the event.
        data: Optional dictionary of additional data to include.
        filename: Name of the log file.
        level: Log level (INFO, WARNING, ERROR, CRITICAL).
        
    Returns:
        The updated log dictionary.
    """
    log_data = load_existing_log(filename)
    
    # Ensure events list exists
    if "events" not in log_data:
        log_data["events"] = []
    
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "level": level,
        "message": message,
        "data": data or {}
    }
    
    log_data["events"].append(event)
    
    # Update metadata
    log_data["last_updated"] = datetime.utcnow().isoformat() + "Z"
    log_data["total_events"] = len(log_data["events"])
    
    write_json_log(log_data, filename)
    return log_data


def setup_logging(log_file: str = "pipeline_log.json") -> logging.Logger:
    """
    Set up the standard Python logging infrastructure to write to both console and JSON file.
    
    Args:
        log_file: Name of the JSON log file to write detailed events to.
        
    Returns:
        Configured logger instance.
    """
    global _logger, _log_file_path
    
    if _logger is not None:
        return _logger
    
    _logger = logging.getLogger("llmXive_pipeline")
    _logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    _logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    _logger.addHandler(console_handler)
    
    # File handler (text)
    log_file_path = get_log_path(log_file.replace('.json', '.log'))
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    _logger.addHandler(file_handler)
    
    _log_file_path = get_log_path(log_file)
    
    return _logger


def log_json_metric(metric_name: str, value, filename: str = "pipeline_log.json") -> None:
    """
    Log a specific metric value to the JSON log.
    
    Args:
        metric_name: Name of the metric.
        value: Value of the metric.
        filename: Name of the log file.
    """
    log_event(
        event_type="METRIC",
        message=f"Recorded metric: {metric_name}",
        data={metric_name: value},
        filename=filename
    )


def get_pipeline_status(filename: str = "pipeline_log.json") -> str:
    """
    Get the current pipeline status from the log file.
    
    Args:
        filename: Name of the log file.
        
    Returns:
        Status string (e.g., "RUNNING", "SUCCESS", "FAILURE") or "UNKNOWN".
    """
    log_data = load_existing_log(filename)
    return log_data.get("pipeline_status", "UNKNOWN")


def update_pipeline_status(status: str, filename: str = "pipeline_log.json") -> None:
    """
    Update the pipeline status in the log file.
    
    Args:
        status: New status string (e.g., "RUNNING", "SUCCESS", "FAILURE").
        filename: Name of the log file.
    """
    log_data = load_existing_log(filename)
    log_data["pipeline_status"] = status
    log_data["last_updated"] = datetime.utcnow().isoformat() + "Z"
    write_json_log(log_data, filename)
    
    # Also log as an event
    log_event(
        event_type="STATUS_UPDATE",
        message=f"Pipeline status updated to: {status}",
        data={"status": status},
        filename=filename
    )
