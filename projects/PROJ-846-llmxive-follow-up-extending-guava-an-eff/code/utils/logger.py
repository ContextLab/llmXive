import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# Ensure the log file path is consistent with project structure
ARTIFACTS_DIR = Path("data/artifacts")
PERCEPTION_LOG_PATH = ARTIFACTS_DIR / "perception_log.json"

def _ensure_log_file():
    """Ensure the perception log file exists and is initialized."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    if not PERCEPTION_LOG_PATH.exists():
        with open(PERCEPTION_LOG_PATH, 'w') as f:
            json.dump([], f)

def _read_log() -> List[Dict[str, Any]]:
    """Read the current contents of the perception log."""
    _ensure_log_file()
    with open(PERCEPTION_LOG_PATH, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def _write_log(entries: List[Dict[str, Any]]) -> None:
    """Write entries back to the perception log file."""
    _ensure_log_file()
    with open(PERCEPTION_LOG_PATH, 'w') as f:
        json.dump(entries, f, indent=2)

def log_perception_ground_truth(
    detected_objects: List[Dict[str, Any]],
    confidence_scores: List[float],
    object_missing_if_visible: bool,
    timestamp: Optional[float] = None
) -> None:
    """
    Log a single perception ground-truth entry to the PerceptionLog.

    This function appends a new entry to the JSON list in data/artifacts/perception_log.json.
    The entry schema matches the specification:
    {
        "timestamp": float,
        "detected_objects": [...],
        "confidence_scores": [...],
        "object_missing_if_visible": boolean
    }

    Args:
        detected_objects: List of dicts with keys: class, bbox, centroid, color_hist.
        confidence_scores: List of float confidence values.
        object_missing_if_visible: Boolean derived from YOLO vs Ground Truth comparison.
        timestamp: Unix timestamp (defaults to current time).
    """
    if timestamp is None:
        timestamp = time.time()

    entry = {
        "timestamp": timestamp,
        "detected_objects": detected_objects,
        "confidence_scores": confidence_scores,
        "object_missing_if_visible": object_missing_if_visible
    }

    current_log = _read_log()
    current_log.append(entry)
    _write_log(current_log)

def log_latency(
    frame_id: str,
    latency_ms: float,
    timestamp: Optional[float] = None
) -> None:
    """
    Add perception latency measurements to the PerceptionLog.

    This function extends the existing perception log entries by appending
    a latency measurement. It assumes the log is a list of entries where
    each entry is a dictionary. If the log is empty, it initializes it.
    If the last entry does not have a 'latencies' key, it creates one.
    If the last entry is not the one corresponding to the current frame,
    it appends a new entry specifically for latency if no matching entry exists.

    However, to strictly follow the schema implied by T016 and FR-007/FR-008,
    where a single JSON file holds the 'Perception Ground-Truth Log',
    we will augment the *latest* entry or create a new entry if the log
    is being populated sequentially by frame.

    For robustness in a pipeline where frames are processed sequentially:
    - We append a new entry if the log is empty or if we assume each call
      corresponds to a new frame processing event.
    - The entry structure for latency will be:
      {
        "timestamp": float,
        "frame_id": str,
        "latency_ms": float,
        "type": "latency_measurement"
      }
    - OR, we append to the 'detected_objects' or a new 'latency' field in the
      existing ground-truth entry if we know the context.

    Given the task description "add perception latency measurements to PerceptionLog",
    and the log is a continuous stream, the safest implementation is to append
    a new log entry specifically for latency, or update the most recent entry
    if it represents the same frame.

    Since T016 writes the ground truth entry, and T018 writes latency, they likely
    correspond to the same processing step. We will attempt to find the most recent
    entry that doesn't have latency yet, or append a new entry.

    To simplify and ensure data integrity: We will append a new entry to the log
    with the latency data. This keeps the log as a chronological list of events.

    Args:
        frame_id: Identifier for the frame being processed.
        latency_ms: Inference latency in milliseconds.
        timestamp: Unix timestamp (defaults to current time).
    """
    if timestamp is None:
        timestamp = time.time()

    latency_entry = {
        "timestamp": timestamp,
        "frame_id": frame_id,
        "latency_ms": latency_ms,
        "type": "latency_measurement"
    }

    current_log = _read_log()
    current_log.append(latency_entry)
    _write_log(current_log)

def get_current_log_stats() -> Dict[str, Any]:
    """
    Retrieve basic statistics from the current PerceptionLog.

    Returns:
        A dictionary containing:
        - total_entries: int
        - latency_entries: int
        - ground_truth_entries: int
        - avg_latency_ms: float (or None if no latency entries)
        - max_latency_ms: float (or None)
    """
    current_log = _read_log()
    if not current_log:
        return {
            "total_entries": 0,
            "latency_entries": 0,
            "ground_truth_entries": 0,
            "avg_latency_ms": None,
            "max_latency_ms": None
        }

    latency_entries = [e for e in current_log if e.get("type") == "latency_measurement"]
    gt_entries = [e for e in current_log if "detected_objects" in e]

    latencies = [e["latency_ms"] for e in latency_entries if "latency_ms" in e]

    return {
        "total_entries": len(current_log),
        "latency_entries": len(latency_entries),
        "ground_truth_entries": len(gt_entries),
        "avg_latency_ms": sum(latencies) / len(latencies) if latencies else None,
        "max_latency_ms": max(latencies) if latencies else None
    }

if __name__ == "__main__":
    # Simple demo to verify the log functions work
    print("Testing logger functions...")
    
    # Test log_perception_ground_truth
    log_perception_ground_truth(
        detected_objects=[{"class": "cup", "bbox": [10, 10, 50, 50], "centroid": [30.0, 30.0], "color_hist": [0.1, 0.2, 0.3]}],
        confidence_scores=[0.95],
        object_missing_if_visible=False
    )
    print("Logged ground truth entry.")

    # Test log_latency
    log_latency(frame_id="frame_001", latency_ms=45.2)
    print("Logged latency entry.")

    # Test stats
    stats = get_current_log_stats()
    print(f"Log stats: {stats}")