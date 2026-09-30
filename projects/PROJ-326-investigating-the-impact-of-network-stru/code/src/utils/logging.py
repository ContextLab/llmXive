import json
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

# Constants
LOG_FILE_PATH = Path("data/run_log.json")
VALID_EVENT_TYPES = {
    "graph_generated",
    "simulation_start",
    "simulation_end",
    "divergence_detected",
    "timeout_reached",
}

def init_logging() -> None:
    """
    Initialize logging infrastructure.
    Creates data/run_log.json as an empty JSON array if it does not exist.
    """
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE_PATH.exists():
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)

def log_metric(event: Dict[str, Any]) -> None:
    """
    Append an entry to the run log.
    
    Args:
        event: A dictionary containing:
            - timestamp: ISO 8601 string
            - event_type: One of the VALID_EVENT_TYPES
            - run_id: String identifier
            - seed: Integer seed
            - status: String status
            - duration_seconds: Float duration
    """
    # Validate schema
    required_keys = {"timestamp", "event_type", "run_id", "seed", "status", "duration_seconds"}
    if set(event.keys()) != required_keys:
        raise ValueError(f"Event must have keys: {required_keys}, got: {set(event.keys())}")
    
    if event["event_type"] not in VALID_EVENT_TYPES:
        raise ValueError(f"Invalid event_type: {event['event_type']}. Must be one of {VALID_EVENT_TYPES}")
    
    # Ensure log file exists
    init_logging()
    
    # Read existing log
    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        log_data = json.load(f)
    
    # Append new entry
    log_data.append(event)
    
    # Write back
    with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)

def get_run_log() -> List[Dict[str, Any]]:
    """
    Load and return the entire run log.
    
    Returns:
        List of log entries.
    """
    init_logging()
    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def log_run(event_type: str, run_id: str, seed: int, status: str, duration_seconds: float) -> None:
    """
    Convenience wrapper to log a run event with auto-generated timestamp.
    
    Args:
        event_type: One of VALID_EVENT_TYPES
        run_id: String identifier
        seed: Integer seed
        status: String status
        duration_seconds: Float duration
    """
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "run_id": run_id,
        "seed": seed,
        "status": status,
        "duration_seconds": duration_seconds,
    }
    log_metric(event)
