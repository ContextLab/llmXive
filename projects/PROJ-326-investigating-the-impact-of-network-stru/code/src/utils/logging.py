"""
Logging infrastructure for the simulation pipeline.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure data directory exists
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

RUN_LOG_PATH = DATA_DIR / "run_log.json"

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/simulation.log")
    ]
)

logger = logging.getLogger(__name__)


def get_run_log() -> List[Dict[str, Any]]:
    """Load the existing run log or return an empty list if it doesn't exist."""
    if not RUN_LOG_PATH.exists():
        return []
    try:
        with open(RUN_LOG_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        logger.warning(f"Could not read {RUN_LOG_PATH}; initializing empty log.")
        return []


def save_run_log(log_data: List[Dict[str, Any]]):
    """Save the run log to disk."""
    with open(RUN_LOG_PATH, "w") as f:
        json.dump(log_data, f, indent=2)


def log_run(
    event_type: str,
    run_id: str,
    seed: int,
    status: str,
    duration_seconds: float,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log a run event to the run log file.
    
    Args:
        event_type: Type of event (e.g., 'graph_generated', 'simulation_start').
        run_id: Unique identifier for the run.
        seed: Random seed used.
        status: Status of the run (e.g., 'success', 'failed').
        duration_seconds: Duration of the run.
        metadata: Optional additional metadata.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "run_id": run_id,
        "seed": seed,
        "status": status,
        "duration_seconds": duration_seconds
    }
    if metadata:
        log_entry["metadata"] = metadata
    
    log_data = get_run_log()
    log_data.append(log_entry)
    save_run_log(log_data)
    logger.info(f"Logged event: {event_type} for run {run_id}")


def log_metric(
    event_type: str,
    run_id: str,
    seed: int,
    status: str,
    duration_seconds: float,
    extra_fields: Optional[Dict[str, Any]] = None
):
    """
    Log a metric event to the run log file.
    
    Args:
        event_type: Type of event (e.g., 'simulation_end', 'divergence_detected').
        run_id: Unique identifier for the run.
        seed: Random seed used.
        status: Status of the run.
        duration_seconds: Duration of the run.
        extra_fields: Optional additional fields to log.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "run_id": run_id,
        "seed": seed,
        "status": status,
        "duration_seconds": duration_seconds
    }
    if extra_fields:
        log_entry.update(extra_fields)
    
    log_data = get_run_log()
    log_data.append(log_entry)
    save_run_log(log_data)
    logger.info(f"Logged metric: {event_type} for run {run_id}")


def initialize_logging():
    """Initialize logging infrastructure and ensure run_log.json exists."""
    if not RUN_LOG_PATH.exists():
        save_run_log([])
        logger.info(f"Initialized empty run log at {RUN_LOG_PATH}")
    else:
        logger.info(f"Run log already exists at {RUN_LOG_PATH}")
