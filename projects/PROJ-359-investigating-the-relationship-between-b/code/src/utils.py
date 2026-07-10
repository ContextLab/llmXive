"""
Utility module for the llmXive research pipeline.

Provides:
- Deterministic random seeding based on RANDOM_SEED environment variable.
- Structured JSON logging infrastructure for pipeline execution.
- Motion threshold constants as defined in the specification.
"""
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# --- Configuration Constants ---
# Motion exclusion threshold in mm (per Spec FR-002 and Constitution Principle VII)
MOTION_THRESHOLD_MM = 3.0

# Default random seed if environment variable is not set
DEFAULT_RANDOM_SEED = 42

# --- Seeding Infrastructure ---
def seed_manager() -> int:
    """
    Initialize deterministic seeding for reproducibility.
    
    Reads the RANDOM_SEED environment variable. If not set, uses DEFAULT_RANDOM_SEED.
    Seeds the random module, numpy, and (optionally) torch if available.
    
    Returns:
        int: The seed value used.
    """
    seed_val = int(os.environ.get("RANDOM_SEED", DEFAULT_RANDOM_SEED))
    
    random.seed(seed_val)
    np.random.seed(seed_val)
    
    # Attempt to seed torch if available (common in ML pipelines)
    try:
        import torch
        torch.manual_seed(seed_val)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed_val)
    except ImportError:
        pass  # Torch not required for this specific pipeline run
        
    return seed_val


# --- JSON Logging Infrastructure ---
def get_log_path() -> Path:
    """
    Returns the path to the pipeline log file.
    """
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "pipeline_log.json"


def load_existing_log() -> Dict[str, Any]:
    """
    Loads the existing log file if it exists, otherwise returns an empty structure.
    """
    log_path = get_log_path()
    if log_path.exists():
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {
                "pipeline_status": "ERROR",
                "error": "Corrupt existing log file",
                "logs": []
            }
    return {
        "pipeline_status": "INITIALIZED",
        "start_time": datetime.utcnow().isoformat(),
        "logs": []
    }


def write_json_log(
    log_path: Optional[Path] = None,
    status: Optional[str] = None,
    exclusion_motion: Optional[int] = None,
    exclusion_missing_wm: Optional[int] = None,
    exclusion_missing_id: Optional[int] = None,
    total_runtime_seconds: Optional[float] = None,
    custom_entries: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Writes or updates the pipeline execution log to `data/logs/pipeline_log.json`.
    
    Args:
        log_path: Optional override for the log file path.
        status: Final pipeline status (e.g., 'SUCCESS', 'FAILED', 'RUNNING').
        exclusion_motion: Count of subjects excluded due to motion.
        exclusion_missing_wm: Count of subjects excluded due to missing WM scores.
        exclusion_missing_id: Count of subjects excluded due to ID mismatch.
        total_runtime_seconds: Total runtime in seconds.
        custom_entries: List of additional log entries to append.
        
    Returns:
        The updated log dictionary.
    """
    log_data = load_existing_log()
    
    if status:
        log_data["pipeline_status"] = status
    
    if total_runtime_seconds is not None:
        log_data["total_runtime_seconds"] = total_runtime_seconds
    
    # Update exclusion counts if provided
    if exclusion_motion is not None:
        log_data["exclusion_motion"] = exclusion_motion
    if exclusion_missing_wm is not None:
        log_data["exclusion_missing_wm"] = exclusion_missing_wm
    if exclusion_missing_id is not None:
        log_data["exclusion_missing_id"] = exclusion_missing_id
        
    if custom_entries:
        if "logs" not in log_data:
            log_data["logs"] = []
        log_data["logs"].extend(custom_entries)
        
    # Ensure end_time is set if status is final
    if status in ("SUCCESS", "FAILED", "ERROR") and "end_time" not in log_data:
        log_data["end_time"] = datetime.utcnow().isoformat()
        
    target_path = log_path or get_log_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, default=str)
        
    return log_data


def log_event(
    event_type: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    log_path: Optional[Path] = None
) -> None:
    """
    Appends a single event to the JSON log.
    
    Args:
        event_type: Type of event (e.g., 'INFO', 'WARNING', 'ERROR', 'EXCLUSION').
        message: Human-readable description.
        data: Optional structured data associated with the event.
        log_path: Optional override for the log file path.
    """
    log_data = load_existing_log()
    if "logs" not in log_data:
        log_data["logs"] = []
        
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": event_type,
        "message": message
    }
    if data:
        entry["data"] = data
        
    log_data["logs"].append(entry)
    
    target_path = log_path or get_log_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, default=str)


# --- Main Execution Block for Testing ---
if __name__ == "__main__":
    # Test seeding
    seed = seed_manager()
    print(f"Seeded RNG with value: {seed}")
    
    # Test logging
    log_event("INFO", "Utils module initialized for testing")
    
    # Test full write
    final_log = write_json_log(
        status="TEST_SUCCESS",
        exclusion_motion=0,
        total_runtime_seconds=1.5,
        custom_entries=[{"type": "TEST", "message": "Verification entry"}]
    )
    print(f"Log written. Status: {final_log.get('pipeline_status')}")
    
    # Verify determinism
    val1 = random.random()
    np_val1 = np.random.rand()
    
    seed_manager() # Re-seed
    val2 = random.random()
    np_val2 = np.random.rand()
    
    assert val1 == val2, "Random seeding failed"
    assert np_val1 == np_val2, "Numpy seeding failed"
    print("Determinism verified.")
