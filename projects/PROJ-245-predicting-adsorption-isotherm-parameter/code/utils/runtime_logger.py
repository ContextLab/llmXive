import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state for the current run
_start_time: Optional[float] = None
_log_data: Dict[str, Any] = {
    "start_time": None,
    "end_time": None,
    "duration_seconds": None,
    "status": "pending",
    "stages": [],
    "error": None
}

def start_timer():
    """Start the global runtime timer and record start timestamp."""
    global _start_time
    _start_time = time.time()
    _log_data["start_time"] = datetime.utcnow().isoformat()
    _log_data["status"] = "running"
    logger.info("Runtime timer started.")

def end_timer(stage_name: str = "final"):
    """Stop the timer and record end timestamp."""
    global _start_time
    if _start_time is None:
        logger.warning("Timer end called without start. Initializing timer.")
        _start_time = time.time()
        _log_data["start_time"] = datetime.utcnow().isoformat()
    
    end_time = time.time()
    _log_data["end_time"] = datetime.utcnow().isoformat()
    _log_data["duration_seconds"] = round(end_time - _start_time, 3)
    _log_data["status"] = "completed"
    
    logger.info(f"Runtime timer stopped. Duration: {_log_data['duration_seconds']}s")
    return _log_data["duration_seconds"]

def fail_timer(error_msg: str):
    """Record a failure state."""
    global _start_time
    if _start_time is None:
        _start_time = time.time()
        _log_data["start_time"] = datetime.utcnow().isoformat()
    
    _log_data["status"] = "failed"
    _log_data["error"] = error_msg
    _log_data["end_time"] = datetime.utcnow().isoformat()
    _log_data["duration_seconds"] = round(time.time() - _start_time, 3)
    
    logger.error(f"Runtime timer failed: {error_msg}")

def get_elapsed_seconds() -> float:
    """Get the current elapsed time since start."""
    if _start_time is None:
        return 0.0
    return round(time.time() - _start_time, 3)

def log_stage(stage_name: str, status: str = "completed", details: Optional[Dict] = None):
    """Log a specific stage of the pipeline."""
    stage_entry = {
        "name": stage_name,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "elapsed_at_stage": get_elapsed_seconds(),
        "details": details or {}
    }
    _log_data["stages"].append(stage_entry)
    logger.info(f"Stage '{stage_name}' logged: {status}")

def persist_runtime_log(output_path: str = "data/benchmarks/runtime_log.json"):
    """
    Persist the runtime log to a JSON file.
    Ensures the directory exists before writing.
    """
    global _log_data
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # If we haven't recorded an end time yet (script crashed before end_timer), capture it now
    if _log_data["end_time"] is None:
        _log_data["end_time"] = datetime.utcnow().isoformat()
        if _log_data["status"] == "running":
            _log_data["status"] = "interrupted"
        _log_data["duration_seconds"] = get_elapsed_seconds()
    
    try:
        with open(path, 'w') as f:
            json.dump(_log_data, f, indent=2)
        logger.info(f"Runtime log persisted to {path.absolute()}")
        return True
    except Exception as e:
        logger.error(f"Failed to persist runtime log: {e}")
        return False

def main():
    """
    Entry point for standalone execution.
    Simulates a run to demonstrate persistence.
    """
    start_timer()
    log_stage("initialization", "completed")
    log_stage("data_loading", "completed", {"rows": 100})
    log_stage("training", "completed", {"model": "rf"})
    
    duration = end_timer()
    persist_runtime_log()
    
    print(f"Runtime log written. Total duration: {duration}s")

if __name__ == "__main__":
    main()
