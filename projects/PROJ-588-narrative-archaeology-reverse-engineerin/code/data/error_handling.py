import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
import numpy as np

# Configure logging for the module
logger = logging.getLogger(__name__)

# Default motion threshold in mm (can be overridden in config)
DEFAULT_MOTION_THRESHOLD_MM = 3.0

def calculate_motion_metrics(translations: np.ndarray, rotations: np.ndarray) -> dict:
    """
    Calculate motion metrics from fMRIPrep transformation parameters.

    Args:
        translations: Array of shape (n_timepoints, 3) containing x, y, z translations (mm).
        rotations: Array of shape (n_timepoints, 3) containing roll, pitch, yaw (radians).

    Returns:
        Dictionary containing:
            - 'max_displacement_mm': Maximum instantaneous displacement (mm).
            - 'mean_displacement_mm': Mean instantaneous displacement (mm).
            - 'max_rotation_deg': Maximum instantaneous rotation (degrees).
            - 'mean_rotation_deg': Mean instantaneous rotation (degrees).
            - 'framedrops': Number of timepoints exceeding the motion threshold.
    """
    if translations.shape[0] != rotations.shape[0]:
        raise ValueError("Translations and rotations must have the same number of timepoints.")

    # Calculate instantaneous displacement (Friston et al. 1996)
    # Displacement = sqrt(dx^2 + dy^2 + dz^2)
    diffs = np.diff(translations, axis=0)
    displacements = np.sqrt(np.sum(diffs**2, axis=1))

    # Calculate instantaneous rotation (in mm, approximated for 50mm radius)
    # Rotation = 50 * sqrt(droll^2 + dpitch^2 + dyaw^2)
    rot_diffs = np.diff(rotations, axis=0)
    rotations_mm = 50.0 * np.sqrt(np.sum(rot_diffs**2, axis=1))

    # Total instantaneous motion
    total_motion = displacements + rotations_mm

    # Convert rotation diffs to degrees for reporting
    rot_diffs_deg = np.degrees(np.linalg.norm(rot_diffs, axis=1))

    max_disp = float(np.max(total_motion))
    mean_disp = float(np.mean(total_motion))
    max_rot = float(np.max(rot_diffs_deg))
    mean_rot = float(np.mean(rot_diffs_deg))

    # Count frames exceeding threshold
    framedrops = int(np.sum(total_motion > DEFAULT_MOTION_THRESHOLD_MM))

    return {
        "max_displacement_mm": max_disp,
        "mean_displacement_mm": mean_disp,
        "max_rotation_deg": max_rot,
        "mean_rotation_deg": mean_rot,
        "framedrops": framedrops,
        "motion_threshold_mm": DEFAULT_MOTION_THRESHOLD_MM
    }

def check_motion_artifacts(metrics: dict, threshold_mm: float = None) -> tuple:
    """
    Check if motion metrics exceed acceptable thresholds.

    Args:
        metrics: Dictionary returned by calculate_motion_metrics.
        threshold_mm: Optional override for the motion threshold.

    Returns:
        Tuple (is_valid, reason):
            - is_valid: True if motion is acceptable, False otherwise.
            - reason: String explaining the decision.
    """
    if threshold_mm is None:
        threshold_mm = DEFAULT_MOTION_THRESHOLD_MM

    max_disp = metrics.get("max_displacement_mm", 0.0)
    framedrops = metrics.get("framedrops", 0)
    total_frames = metrics.get("total_frames", 0) # Optional context

    # Criterion 1: Maximum displacement exceeds threshold
    if max_disp > threshold_mm:
        return False, f"Max displacement ({max_disp:.2f}mm) exceeds threshold ({threshold_mm}mm)"

    # Criterion 2: Excessive number of censored frames (>20% of total)
    if total_frames > 0 and framedrops > 0.2 * total_frames:
        return False, f"Excessive motion censoring: {framedrops} frames ({100*framedrops/total_frames:.1f}%) exceed threshold"

    return True, "Motion metrics within acceptable limits"

def log_error(error_log_path: Path, subject_id: str, error_code: str, details: dict):
    """
    Log an error to a JSON-formatted log file.

    Args:
        error_log_path: Path to the error log file.
        subject_id: Identifier for the subject.
        error_code: Short code for the error type (e.g., 'MOTION', 'MISSING_FILE').
        details: Dictionary of additional error details.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "subject_id": subject_id,
        "error_code": error_code,
        **details
    }

    # Ensure directory exists
    error_log_path.parent.mkdir(parents=True, exist_ok=True)

    # Append to log file
    with open(error_log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')

    logger.warning(f"Logged error for {subject_id}: {error_code} - {details}")

def handle_subject_error(subject_id: str, error_type: str, metrics: dict = None, error_log_path: Path = None):
    """
    Handle a subject error by checking motion and logging if necessary.

    Args:
        subject_id: Subject identifier.
        error_type: Type of error (e.g., 'MOTION_ARTIFACT', 'PREPROCESSING_FAILED').
        metrics: Optional motion metrics dictionary.
        error_log_path: Path to the error log file. Defaults to 'data/errors.log'.

    Returns:
        bool: True if the subject should be skipped (error logged), False otherwise.
    """
    if error_log_path is None:
        error_log_path = Path("data/errors.log")

    if error_type == "MOTION_ARTIFACT" and metrics:
        is_valid, reason = check_motion_artifacts(metrics)
        if not is_valid:
            log_error(
                error_log_path,
                subject_id,
                "MOTION_ARTIFACT",
                {
                    "motion_mm": metrics.get("max_displacement_mm", 0.0),
                    "framedrops": metrics.get("framedrops", 0),
                    "reason": reason
                }
            )
            return True
    elif error_type:
        # Log other errors without motion metrics
        log_error(
            error_log_path,
            subject_id,
            error_type,
            {"reason": "Unspecified processing failure"}
        )
        return True

    return False

def get_error_summary(error_log_path: Path) -> dict:
    """
    Generate a summary of errors from the log file.

    Args:
        error_log_path: Path to the error log file.

    Returns:
        Dictionary with counts of errors by type and subject list.
    """
    if not error_log_path.exists():
        return {"total_errors": 0, "by_code": {}, "subjects": []}

    errors = []
    with open(error_log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                errors.append(json.loads(line))

    by_code = {}
    subjects = set()
    for err in errors:
        code = err.get("error_code", "UNKNOWN")
        by_code[code] = by_code.get(code, 0) + 1
        subjects.add(err.get("subject_id", "UNKNOWN"))

    return {
        "total_errors": len(errors),
        "by_code": by_code,
        "subjects": list(subjects)
    }

def clear_error_log(error_log_path: Path = None):
    """
    Clear the error log file.

    Args:
        error_log_path: Path to the error log file. Defaults to 'data/errors.log'.
    """
    if error_log_path is None:
        error_log_path = Path("data/errors.log")

    if error_log_path.exists():
        error_log_path.unlink()
        logger.info(f"Cleared error log at {error_log_path}")
    else:
        logger.info(f"No error log found at {error_log_path} to clear.")
