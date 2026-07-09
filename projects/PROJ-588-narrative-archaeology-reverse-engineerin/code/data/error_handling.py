"""
Error handling infrastructure for the Narrative Archaeology pipeline.

Provides utilities to detect motion artifacts in fMRI data, skip problematic
subjects, and log errors in a structured JSON format to data/errors.log.
"""
import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np

import code.config as config

# Configure logging
logger = logging.getLogger(__name__)

# Ensure data directory exists
DATA_DIR = Path(config.DATA_DIR)
DATA_DIR.mkdir(parents=True, exist_ok=True)

ERROR_LOG_PATH = DATA_DIR / "errors.log"


def calculate_motion_metrics(
    displacement: np.ndarray,
    rotation: np.ndarray,
    voxel_size: float = 3.0
) -> Dict[str, float]:
    """
    Calculate motion metrics from displacement and rotation parameters.

    Args:
        displacement: Array of translational displacements (mm) per volume [N, 3]
        rotation: Array of rotational displacements (radians) per volume [N, 3]
        voxel_size: Approximate voxel size in mm for rotation conversion

    Returns:
        Dictionary containing:
            - mean_displacement: Mean translational displacement (mm)
            - max_displacement: Maximum translational displacement (mm)
            - mean_rotation_mm: Mean rotational displacement converted to mm
            - max_rotation_mm: Maximum rotational displacement converted to mm
            - framewise_displacement: Sum of absolute motion metrics per frame
    """
    if displacement.shape[0] == 0:
        return {
            "mean_displacement": 0.0,
            "max_displacement": 0.0,
            "mean_rotation_mm": 0.0,
            "max_rotation_mm": 0.0,
            "framewise_displacement": np.array([])
        }

    # Translational metrics
    translational_norm = np.linalg.norm(displacement, axis=1)
    mean_disp = float(np.mean(translational_norm))
    max_disp = float(np.max(translational_norm))

    # Convert rotation to mm (approximate arc length at edge of brain)
    # Assuming brain radius ~50mm, but using voxel_size as a proxy for local scale
    rotation_mm = np.abs(rotation) * voxel_size * 50.0 / 3.0  # Approximate conversion
    mean_rot_mm = float(np.mean(np.linalg.norm(rotation_mm, axis=1)))
    max_rot_mm = float(np.max(np.linalg.norm(rotation_mm, axis=1)))

    # Framewise displacement (Power et al., 2012)
    # FD = sum(|dX|) + sum(|dY|) + sum(|dZ|) + sum(|dPitch|*R) + ...
    fd = (
        np.sum(np.abs(np.diff(displacement, axis=0)), axis=1) +
        np.sum(np.abs(np.diff(rotation, axis=0)) * voxel_size * 50.0 / 3.0, axis=1)
    )

    return {
        "mean_displacement": mean_disp,
        "max_displacement": max_disp,
        "mean_rotation_mm": mean_rot_mm,
        "max_rotation_mm": max_rot_mm,
        "framewise_displacement": fd
    }


def check_motion_artifacts(
    displacement: np.ndarray,
    rotation: np.ndarray,
    voxel_size: float = 3.0,
    threshold_mm: Optional[float] = None
) -> Dict[str, Any]:
    """
    Check if motion exceeds thresholds and determine if subject should be skipped.

    Args:
        displacement: Translational displacements [N, 3] in mm
        rotation: Rotational displacements [N, 3] in radians
        voxel_size: Voxel size in mm
        threshold_mm: Motion threshold in mm (defaults to config.MOTION_THRESHOLD_MM)

    Returns:
        Dictionary containing:
            - is_rejected: True if subject should be skipped
            - reason: String explaining rejection (or None)
            - metrics: Dictionary of calculated motion metrics
    """
    if threshold_mm is None:
        threshold_mm = config.MOTION_THRESHOLD_MM

    metrics = calculate_motion_metrics(displacement, rotation, voxel_size)

    # Rejection criteria:
    # 1. Mean FD > threshold
    # 2. Any single frame FD > 3 * threshold
    # 3. > 20% of frames have FD > threshold

    mean_fd = float(np.mean(metrics["framewise_displacement"])) if len(metrics["framewise_displacement"]) > 0 else 0.0
    max_fd = float(np.max(metrics["framewise_displacement"])) if len(metrics["framewise_displacement"]) > 0 else 0.0
    high_motion_ratio = float(np.sum(metrics["framewise_displacement"] > threshold_mm) / len(metrics["framewise_displacement"])) if len(metrics["framewise_displacement"]) > 0 else 0.0

    is_rejected = False
    reason = None

    if mean_fd > threshold_mm:
        is_rejected = True
        reason = f"Mean FD ({mean_fd:.3f}mm) exceeds threshold ({threshold_mm}mm)"
    elif max_fd > 3 * threshold_mm:
        is_rejected = True
        reason = f"Maximum FD ({max_fd:.3f}mm) exceeds 3x threshold ({3 * threshold_mm}mm)"
    elif high_motion_ratio > 0.20:
        is_rejected = True
        reason = f"High motion ratio ({high_motion_ratio:.1%}) exceeds 20% threshold"

    return {
        "is_rejected": is_rejected,
        "reason": reason,
        "metrics": metrics
    }


def log_error(
    subject_id: str,
    error_code: str,
    error_message: str,
    additional_data: Optional[Dict[str, Any]] = None,
    motion_mm: float = 0.0
) -> None:
    """
    Log an error to the structured JSON error log.

    Args:
        subject_id: Identifier for the subject
        error_code: Short code for the error type (e.g., "MOTION_ARTIFACT")
        error_message: Human-readable error description
        additional_data: Optional dictionary of additional context
        motion_mm: Motion metric value if applicable
    """
    error_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "subject_id": subject_id,
        "error_code": error_code,
        "error_message": error_message,
        "motion_mm": motion_mm
    }

    if additional_data:
        error_entry.update(additional_data)

    # Append to log file
    with open(ERROR_LOG_PATH, "a") as f:
        f.write(json.dumps(error_entry) + "\n")

    logger.warning(f"Error logged for {subject_id}: {error_code} - {error_message}")


def handle_subject_error(
    subject_id: str,
    error_code: str,
    error_message: str,
    motion_metrics: Optional[Dict[str, float]] = None,
    skip: bool = True
) -> bool:
    """
    Handle an error for a subject, optionally skipping further processing.

    Args:
        subject_id: Subject identifier
        error_code: Error code
        error_message: Error description
        motion_metrics: Motion metrics dictionary if applicable
        skip: Whether to skip further processing (default True)

    Returns:
        True if subject was skipped, False otherwise
    """
    motion_mm = motion_metrics.get("mean_displacement", 0.0) if motion_metrics else 0.0

    log_error(
        subject_id=subject_id,
        error_code=error_code,
        error_message=error_message,
        motion_mm=motion_mm
    )

    if skip:
        logger.info(f"Skipping subject {subject_id} due to {error_code}")
        return True

    return False


def get_error_summary() -> List[Dict[str, Any]]:
    """
    Read and return all logged errors as a list of dictionaries.

    Returns:
        List of error entries
    """
    if not ERROR_LOG_PATH.exists():
        return []

    errors = []
    with open(ERROR_LOG_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    errors.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in error log: {line}")

    return errors


def clear_error_log() -> None:
    """
    Clear the error log file.
    """
    if ERROR_LOG_PATH.exists():
        ERROR_LOG_PATH.unlink()
        logger.info("Error log cleared")
