import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from utils.config import get_path, get_hyperparameter
from utils.errors import DatasetUnavailableError, GroundTruthSchemaMissingError
from data.models import PerceptionLog, SymbolicObservation, serialize_perception_log


def compare_with_gt(
    detected_objects: List[Dict[str, Any]],
    ground_truth_objects: List[Dict[str, Any]],
    iou_threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Compare detected objects against ground truth using IoU and greedy matching.

    Args:
        detected_objects: List of dicts with 'bbox' (x_min, y_min, x_max, y_max) and 'class'.
        ground_truth_objects: List of dicts with 'bbox' and 'class'.
        iou_threshold: Minimum IoU to consider a match.

    Returns:
        Dict containing:
            - object_missing_if_visible: True if a GT object has no match.
            - gt_missing: True if GT was not available/verified.
            - matches: List of (det_idx, gt_idx) tuples.
    """
    if not ground_truth_objects:
        # If GT list is empty, we don't know if it's missing or just empty scene.
        # Per task T016a logic: if status "missing" -> object_missing_if_visible="unknown", gt_missing=true.
        # If status "valid" but empty list -> object_missing_if_visible=false (no objects to miss).
        # We assume this function is called only after verifying GT status.
        # Default assumption: if list is empty, no objects to miss.
        return {
            "object_missing_if_visible": False,
            "gt_missing": False,
            "matches": []
        }

    def calculate_iou(box1: List[float], box2: List[float]) -> float:
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection
        if union == 0:
            return 0.0
        return intersection / union

    matches = []
    matched_gt_indices = set()

    # Greedy matching: iterate detected, find best GT match
    for d_idx, det_obj in enumerate(detected_objects):
        best_iou = -1
        best_gt_idx = -1
        for g_idx, gt_obj in enumerate(ground_truth_objects):
            if g_idx in matched_gt_indices:
                continue
            iou = calculate_iou(det_obj['bbox'], gt_obj['bbox'])
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = g_idx

        if best_iou >= iou_threshold:
            matches.append((d_idx, best_gt_idx))
            matched_gt_indices.add(best_gt_idx)

    # Check for missing GT objects
    missing_gt = len(ground_truth_objects) - len(matched_gt_indices) > 0
    return {
        "object_missing_if_visible": missing_gt,
        "gt_missing": False,
        "matches": matches
    }


def log_perception_ground_truth(
    timestamp: float,
    detected_objects: List[Dict[str, Any]],
    confidence_scores: List[float],
    ground_truth_status: str,  # "valid" or "missing"
    ground_truth_objects: Optional[List[Dict[str, Any]]] = None,
    iou_threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Generate the perception ground truth log entry.

    Args:
        timestamp: Unix timestamp of the frame.
        detected_objects: List of detected object dicts (bbox, class, etc.).
        confidence_scores: List of confidence scores corresponding to detected_objects.
        ground_truth_status: "valid" if GT file verified, "missing" otherwise.
        ground_truth_objects: List of GT object dicts if status is "valid", else None.
        iou_threshold: IoU threshold for matching (default 0.5).

    Returns:
        Dict with keys:
            - timestamp: float
            - detected_objects: list
            - confidence_scores: list
            - object_missing_if_visible: bool | "unknown"
            - gt_missing: bool
    """
    log_entry = {
        "timestamp": timestamp,
        "detected_objects": detected_objects,
        "confidence_scores": confidence_scores,
        "object_missing_if_visible": "unknown",
        "gt_missing": False
    }

    if ground_truth_status == "missing":
        log_entry["object_missing_if_visible"] = "unknown"
        log_entry["gt_missing"] = True
    elif ground_truth_status == "valid":
        if ground_truth_objects is None:
            # Valid status but no objects provided -> treat as empty scene
            log_entry["object_missing_if_visible"] = False
            log_entry["gt_missing"] = False
        else:
            comparison = compare_with_gt(detected_objects, ground_truth_objects, iou_threshold)
            log_entry["object_missing_if_visible"] = comparison["object_missing_if_visible"]
            log_entry["gt_missing"] = False
    else:
        raise ValueError(f"Invalid ground_truth_status: {ground_truth_status}")

    return log_entry


def log_latency(
    task_id: str,
    frame_index: int,
    inference_time_ms: float,
    total_frame_time_ms: float,
    log_path: Optional[Path] = None
) -> PerceptionLog:
    """
    Create and optionally write a PerceptionLog entry for latency tracking.

    Args:
        task_id: Identifier for the task/trajectory.
        frame_index: Index of the frame within the trajectory.
        inference_time_ms: Time spent in YOLO inference (ms).
        total_frame_time_ms: Total time for frame processing (ms).
        log_path: Optional path to append the log entry.

    Returns:
        PerceptionLog dataclass instance.
    """
    log_entry = PerceptionLog(
        task_id=task_id,
        frame_index=frame_index,
        timestamp=datetime.utcnow().isoformat(),
        inference_time_ms=inference_time_ms,
        total_frame_time_ms=total_frame_time_ms,
        latency_threshold_ms=get_hyperparameter("perception_latency_threshold", 150.0)
    )

    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(serialize_perception_log(log_entry) + '\n')

    return log_entry


def get_current_log_stats(log_path: Path) -> Dict[str, Any]:
    """
    Aggregate statistics from the perception log file.

    Args:
        log_path: Path to the perception log file.

    Returns:
        Dict with keys:
            - total_frames: int
            - avg_inference_time_ms: float
            - max_inference_time_ms: float
            - latency_violations: int (frames exceeding threshold)
    """
    if not log_path.exists():
        return {
            "total_frames": 0,
            "avg_inference_time_ms": 0.0,
            "max_inference_time_ms": 0.0,
            "latency_violations": 0
        }

    inference_times = []
    latency_threshold = get_hyperparameter("perception_latency_threshold", 150.0)
    violations = 0

    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                inference_times.append(entry['inference_time_ms'])
                if entry['inference_time_ms'] > latency_threshold:
                    violations += 1
            except (json.JSONDecodeError, KeyError):
                continue

    if not inference_times:
        return {
            "total_frames": 0,
            "avg_inference_time_ms": 0.0,
            "max_inference_time_ms": 0.0,
            "latency_violations": 0
        }

    return {
        "total_frames": len(inference_times),
        "avg_inference_time_ms": sum(inference_times) / len(inference_times),
        "max_inference_time_ms": max(inference_times),
        "latency_violations": violations
    }


def clear_log(log_path: Path) -> None:
    """
    Clear the perception log file.

    Args:
        log_path: Path to the log file.
    """
    if log_path.exists():
        log_path.unlink()