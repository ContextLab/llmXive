import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple

from utils.config import get_path, get_hyperparameter
from utils.exceptions import DatasetUnavailableError

# Constants
PERCEPTION_LOG_PATH = "data/artifacts/perception_log.json"
LATENCY_LOG_PATH = "data/artifacts/latency_log.json"

def _ensure_log_file(log_path: str) -> Path:
    """Ensure the log file and its parent directory exist."""
    path = get_path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, 'w') as f:
            json.dump([], f)
    return path

def _load_log_entries(log_path: str) -> List[Dict[str, Any]]:
    """Load existing entries from the log file."""
    path = _ensure_log_file(log_path)
    try:
        with open(path, 'r') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def _append_to_log(log_path: str, new_entry: Dict[str, Any]) -> None:
    """Append a new entry to the log file atomically."""
    path = _ensure_log_file(log_path)
    entries = _load_log_entries(log_path)
    entries.append(new_entry)
    
    # Atomic write
    temp_path = path.with_suffix('.tmp')
    with open(temp_path, 'w') as f:
        json.dump(entries, f, indent=2)
    os.replace(temp_path, path)

def log_perception_ground_truth(
    timestamp: float,
    detected_objects: List[Dict[str, Any]],
    confidence_scores: List[float],
    ground_truth_objects: Optional[List[Dict[str, Any]]] = None,
    object_missing_if_visible: bool = False
) -> None:
    """
    Log perception ground truth data to the perception log.
    
    Args:
        timestamp: Unix timestamp of the perception event.
        detected_objects: List of detected objects with class, bbox, centroid, color_hist.
        confidence_scores: List of confidence scores for each detection.
        ground_truth_objects: Optional list of ground truth objects for comparison.
        object_missing_if_visible: Boolean indicating if a visible object was missed.
    """
    entry = {
        "timestamp": timestamp,
        "detected_objects": detected_objects,
        "confidence_scores": confidence_scores,
        "object_missing_if_visible": object_missing_if_visible,
        "ground_truth_objects": ground_truth_objects or []
    }
    
    _append_to_log(PERCEPTION_LOG_PATH, entry)

def log_latency(
    task_id: str,
    frame_index: int,
    latency_ms: float,
    threshold_ms: float = 150.0,
    success: bool = True,
    error_message: Optional[str] = None
) -> None:
    """
    Log latency measurement for a specific frame in a task.
    
    Args:
        task_id: Identifier for the task.
        frame_index: Index of the frame being processed.
        latency_ms: Measured latency in milliseconds.
        threshold_ms: Latency threshold for failure classification.
        success: Whether the perception step succeeded.
        error_message: Optional error message if success is False.
    """
    entry = {
        "task_id": task_id,
        "frame_index": frame_index,
        "latency_ms": latency_ms,
        "threshold_ms": threshold_ms,
        "exceeds_threshold": latency_ms > threshold_ms,
        "success": success,
        "timestamp": time.time()
    }
    
    if not success and error_message:
        entry["error_message"] = error_message
    
    _append_to_log(LATENCY_LOG_PATH, entry)

def get_current_log_stats(log_path: str) -> Dict[str, Any]:
    """
    Get statistics about the current log file.
    
    Args:
        log_path: Path to the log file.
        
    Returns:
        Dictionary containing count, average latency (if applicable), 
        and latest timestamp.
    """
    entries = _load_log_entries(log_path)
    
    if not entries:
        return {
            "entry_count": 0,
            "average_latency_ms": None,
            "latest_timestamp": None,
            "exceeds_threshold_count": 0
        }
    
    # Calculate stats based on log type
    if "latency" in log_path:
        latencies = [e.get("latency_ms", 0) for e in entries if "latency_ms" in e]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        exceeds_count = sum(1 for e in entries if e.get("exceeds_threshold", False))
        
        return {
            "entry_count": len(entries),
            "average_latency_ms": avg_latency,
            "latest_timestamp": max(e.get("timestamp", 0) for e in entries) if entries else None,
            "exceeds_threshold_count": exceeds_count
        }
    else:
        # Perception log stats
        return {
            "entry_count": len(entries),
            "latest_timestamp": max(e.get("timestamp", 0) for e in entries) if entries else None,
            "missing_object_count": sum(1 for e in entries if e.get("object_missing_if_visible", False))
        }

def clear_log(log_path: str) -> None:
    """Clear all entries from a log file."""
    path = get_path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump([], f)