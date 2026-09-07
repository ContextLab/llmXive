import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from utils.config import ensure_directories
from data.models import PerceptionLog, PerceptionQuality


# Global state for the current log file path
_LOG_FILE_PATH: Optional[str] = None
_CURRENT_TRAJECTORY_ID: Optional[str] = None


def _get_log_path() -> Path:
    """Resolve the path to the perception log file."""
    if _LOG_FILE_PATH is None:
        # Default location if not explicitly set by context
        base = Path("projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/artifacts")
        ensure_directories([str(base)])
        return base / "perception_log.json"
    return Path(_LOG_FILE_PATH)


def _load_existing_log() -> List[Dict[str, Any]]:
    """Load existing log entries if the file exists, otherwise return empty list."""
    log_path = _get_log_path()
    if log_path.exists():
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, IOError):
            # If corrupted or unreadable, start fresh to avoid crashes
            return []
    return []


def _save_log(entries: List[Dict[str, Any]]) -> None:
    """Save the log entries back to the file."""
    log_path = _get_log_path()
    ensure_directories([str(log_path.parent)])
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, default=str)


def log_perception_ground_truth(
    trajectory_id: str,
    frame_id: int,
    timestamp: datetime,
    objects_detected: List[Dict[str, Any]],
    ground_truth_objects: List[Dict[str, Any]],
    object_missing_if_visible: bool,
    quality: Optional[PerceptionQuality] = None,
) -> None:
    """
    Logs a frame's perception results and ground truth comparison to the continuous PerceptionLog.
    
    Args:
        trajectory_id: The ID of the current trajectory being processed.
        frame_id: The index of the frame within the trajectory.
        timestamp: The UTC timestamp of the processing.
        objects_detected: List of detected objects (bbox, class, centroid, etc.).
        ground_truth_objects: List of ground truth objects for comparison.
        object_missing_if_visible: Flag indicating if a visible object was missed.
        quality: Optional perception quality metric.
    """
    global _CURRENT_TRAJECTORY_ID
    _CURRENT_TRAJECTORY_ID = trajectory_id

    entry = {
        "trajectory_id": trajectory_id,
        "frame_id": frame_id,
        "timestamp": timestamp.isoformat(),
        "objects_detected": objects_detected,
        "ground_truth_objects": ground_truth_objects,
        "object_missing_if_visible": object_missing_if_visible,
        "quality": quality.value if quality else None,
    }

    entries = _load_existing_log()
    entries.append(entry)
    _save_log(entries)


def log_latency(
    trajectory_id: str,
    frame_id: int,
    inference_time_ms: float,
    total_processing_time_ms: float,
    frame_size: tuple,
    model_version: str = "yolov8n.onnx",
) -> None:
    """
    Logs perception latency measurements to the PerceptionLog.
    
    This function records the time taken for the YOLO inference step and the total
    processing time for a specific frame. It enriches the PerceptionLog with
    performance metrics required for FR-007 and FR-008 (latency tracking).
    
    Args:
        trajectory_id: The ID of the current trajectory.
        frame_id: The index of the frame.
        inference_time_ms: Time spent in the YOLO model inference (ms).
        total_processing_time_ms: Total time from frame load to output generation (ms).
        frame_size: Tuple (height, width) of the input frame.
        model_version: The version or name of the ONNX model used.
    """
    global _CURRENT_TRAJECTORY_ID
    if _CURRENT_TRAJECTORY_ID is None:
        _CURRENT_TRAJECTORY_ID = trajectory_id
    
    # Load existing log to append latency data
    entries = _load_existing_log()
    
    # We need to find the entry for this specific trajectory/frame if it exists
    # to merge latency data with the perception ground truth data, OR append a new
    # latency-specific entry if the log structure allows mixed types.
    # Based on the schema, we will append a new entry specifically for latency
    # to maintain a continuous stream of events, or update the last matching entry.
    # To ensure FR-007 (tracking) is met, we append a dedicated latency record.
    
    latency_entry = {
        "trajectory_id": trajectory_id,
        "frame_id": frame_id,
        "timestamp": datetime.now().isoformat(),
        "type": "latency_measurement",
        "metrics": {
            "inference_time_ms": round(inference_time_ms, 3),
            "total_processing_time_ms": round(total_processing_time_ms, 3),
            "frame_height": frame_size[0],
            "frame_width": frame_size[1],
            "model_version": model_version,
        },
        "latency_threshold_exceeded": total_processing_time_ms > 150.0,
    }
    
    entries.append(latency_entry)
    _save_log(entries)


def get_current_log_stats() -> Dict[str, Any]:
    """
    Calculates basic statistics from the current perception log.
    
    Returns:
        A dictionary containing total frames, count of latency violations, etc.
    """
    entries = _load_existing_log()
    
    total_frames = len(entries)
    latency_violations = 0
    missing_objects = 0
    
    for entry in entries:
        if entry.get("type") == "latency_measurement":
            if entry.get("metrics", {}).get("total_processing_time_ms", 0) > 150.0:
                latency_violations += 1
        if entry.get("object_missing_if_visible", False):
            missing_objects += 1
            
    return {
        "total_frames_logged": total_frames,
        "latency_violations_count": latency_violations,
        "missing_objects_count": missing_objects,
        "log_file_path": str(_get_log_path()),
    }