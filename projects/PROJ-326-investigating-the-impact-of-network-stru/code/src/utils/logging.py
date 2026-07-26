import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

LOG_FILE_PATH = Path("data/run_log.json")

def _ensure_log_file():
    """
    Ensures data/run_log.json exists and is a valid JSON array.
    Creates it if missing or invalid.
    """
    if not LOG_FILE_PATH.parent.exists():
        LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    if not LOG_FILE_PATH.exists():
        LOG_FILE_PATH.write_text("[]")
        return

    try:
        with open(LOG_FILE_PATH, "r") as f:
            content = f.read().strip()
            if not content:
                LOG_FILE_PATH.write_text("[]")
            else:
                # Try to parse to ensure it's valid JSON
                data = json.loads(content)
                if not isinstance(data, list):
                    # If it's not a list, reset to empty list
                    LOG_FILE_PATH.write_text("[]")
    except json.JSONDecodeError:
        # If corrupted, reset to empty list
        LOG_FILE_PATH.write_text("[]")

def _save_log(entries: List[Dict[str, Any]]):
    """
    Saves the list of log entries to disk.
    """
    _ensure_log_file()
    with open(LOG_FILE_PATH, "w") as f:
        json.dump(entries, f, indent=2)

def load_log() -> List[Dict[str, Any]]:
    """
    Loads the existing log entries.
    """
    _ensure_log_file()
    with open(LOG_FILE_PATH, "r") as f:
        return json.load(f)

def get_run_log() -> List[Dict[str, Any]]:
    """
    Alias for load_log for compatibility.
    """
    return load_log()

def log_run(
    event_type: str,
    run_id: Optional[str] = None,
    seed: Optional[int] = None,
    message: Optional[str] = None,
    duration_ms: Optional[float] = None,
    status: str = "SUCCESS",
    **kwargs
) -> Dict[str, Any]:
    """
    Logs a run event to data/run_log.json.
    Schema: { timestamp, event_type, run_id, seed, duration_ms, status, ... }
    """
    entries = load_log()
    
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "run_id": run_id or f"run_{int(time.time())}",
        "seed": seed,
        "status": status,
        "message": message
    }
    
    if duration_ms is not None:
        entry["duration_ms"] = duration_ms
    
    # Add any extra kwargs
    entry.update(kwargs)
    
    entries.append(entry)
    _save_log(entries)
    
    logging.info(f"Logged event: {event_type} - {message}")
    return entry

def log_metric(
    metric_name: str,
    value: Any,
    run_id: Optional[str] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Logs a specific metric value.
    """
    return log_run(
        event_type="metric",
        run_id=run_id,
        seed=seed,
        message=f"Metric: {metric_name}",
        metric_name=metric_name,
        metric_value=value
    )

def log_graph_generated(graph_id: str, topology: str, seed: int, run_id: Optional[str] = None):
    """
    Specific helper for T005 graph generated event.
    """
    return log_run(
        event_type="graph_generated",
        run_id=run_id,
        seed=seed,
        message=f"Graph {graph_id} generated",
        graph_id=graph_id,
        topology=topology
    )

def log_simulation_start(run_id: str, seed: int):
    """
    Specific helper for T005 simulation start event.
    """
    return log_run(
        event_type="simulation_start",
        run_id=run_id,
        seed=seed,
        message="Simulation started"
    )

def log_simulation_end(run_id: str, duration_ms: float, status: str = "SUCCESS"):
    """
    Specific helper for T005 simulation end event.
    """
    return log_run(
        event_type="simulation_end",
        run_id=run_id,
        duration_ms=duration_ms,
        status=status,
        message="Simulation ended"
    )

def log_divergence_detected(run_id: str, seed: int):
    """
    Specific helper for T005 divergence detected event.
    """
    return log_run(
        event_type="divergence_detected",
        run_id=run_id,
        seed=seed,
        status="WARNING",
        message="Simulation divergence detected"
    )

def log_timeout_reached(run_id: str, seed: int):
    """
    Specific helper for T005 timeout reached event.
    """
    return log_run(
        event_type="timeout_reached",
        run_id=run_id,
        seed=seed,
        status="FAILURE",
        message="Simulation timeout reached"
    )
