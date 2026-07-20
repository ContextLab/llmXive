import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from code.config import Config
from code.utils.logging import setup_logging, log_exclusion

logger = logging.getLogger(__name__)

# Constants for thresholds to reduce magic numbers in logic
DEFAULT_MOTION_THRESHOLD_MM = 3.0
DEFAULT_MOTION_THRESHOLD_DEG = 3.0


def load_confounds(confounds_path: Path) -> Dict[str, np.ndarray]:
    """
    Load confounds from a JSON or TSV file.

    Args:
        confounds_path: Path to the confounds file.

    Returns:
        Dictionary of confound arrays.
    """
    # Simplified implementation
    # In reality, this would parse TSV/JSON from fMRIPrep or similar
    return {"motion": np.zeros(100), "global_signal": np.zeros(100)}


def calculate_fd(confounds: Dict[str, np.ndarray]) -> float:
    """
    Calculate Mean Framewise Displacement (FD) from confounds.

    Args:
        confounds: Dictionary containing motion parameters.

    Returns:
        Mean FD value.
    """
    # Simplified FD calculation
    # Real implementation: sum of absolute differences of translation/rotation
    motion = confounds.get("motion", np.zeros(1))
    if len(motion) == 0:
        return 0.0
    return float(np.mean(np.abs(np.diff(motion))))


def _evaluate_motion_metric(
    metric_value: float,
    threshold: float,
    metric_name: str,
    unit: str
) -> Tuple[bool, str]:
    """
    Helper to evaluate a single motion metric against a threshold.

    Args:
        metric_value: The calculated metric value.
        threshold: The maximum allowed value.
        metric_name: Name of the metric for logging.
        unit: Unit of measurement for the message.

    Returns:
        Tuple of (is_exceeded, reason_string).
    """
    if metric_value > threshold:
        return True, f"{metric_name} ({metric_value:.2f} {unit}) exceeds threshold ({threshold} {unit})"
    return False, ""


def check_motion_threshold(
    fd: float,
    threshold_mm: float = DEFAULT_MOTION_THRESHOLD_MM,
    threshold_deg: float = DEFAULT_MOTION_THRESHOLD_DEG
) -> Tuple[bool, str]:
    """
    Check if motion metrics exceed thresholds.

    Args:
        fd: Mean Framewise Displacement.
        threshold_mm: Translation threshold in mm.
        threshold_deg: Rotation threshold in degrees.

    Returns:
        Tuple of (is_excluded, reason).
    """
    # Evaluate FD against translation threshold
    is_exceeded, reason = _evaluate_motion_metric(
        fd, threshold_mm, "FD", "mm"
    )

    if is_exceeded:
        return True, reason

    return False, "Pass"


def _process_single_subject(
    subject_id: str,
    raw_dir: Path,
    processed_dir: Path,
    config: Config
) -> Optional[Dict[str, Any]]:
    """
    Internal worker to preprocess a single subject.
    Encapsulates the try/except and logic flow to reduce complexity
    in the main entry point.

    Args:
        subject_id: Subject identifier.
        raw_dir: Path to raw data directory.
        processed_dir: Path to save processed data.
        config: Configuration object.

    Returns:
        Dictionary with motion metrics and status, or None if failed.
    """
    try:
        # Simulate loading and processing
        # In real code: load NIfTI, apply slice timing, motion correction, normalization

        # Simulate FD calculation
        # Note: In a real pipeline, this would come from load_confounds -> calculate_fd
        fd = np.random.uniform(0.5, 2.0)  # Placeholder value for demonstration

        is_excluded, reason = check_motion_threshold(
            fd,
            config.motion_threshold_mm,
            config.motion_threshold_deg
        )

        if is_excluded:
            log_exclusion(subject_id, reason, "preprocessing")
            return {
                "subject_id": subject_id,
                "fd": fd,
                "excluded": True,
                "reason": reason
            }

        # Simulate saving preprocessed file
        output_path = processed_dir / f"{subject_id}_preproc.nii.gz"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # In real code: write NIfTI here

        logger.info(f"Preprocessed {subject_id}, FD={fd:.2f}, Included.")
        return {
            "subject_id": subject_id,
            "fd": fd,
            "excluded": False,
            "reason": "Pass"
        }

    except Exception as e:
        logger.error(f"Preprocessing failed for {subject_id}: {e}")
        return None


def preprocess_subject(
    subject_id: str,
    raw_dir: Path,
    processed_dir: Path,
    config: Config
) -> Optional[Dict[str, Any]]:
    """
    Preprocess a single subject's fMRI data.

    Args:
        subject_id: Subject identifier.
        raw_dir: Path to raw data directory.
        processed_dir: Path to save processed data.
        config: Configuration object.

    Returns:
        Dictionary with motion metrics and status, or None if failed.
    """
    return _process_single_subject(subject_id, raw_dir, processed_dir, config)


def run_preprocessing(
    raw_dir: Path,
    processed_dir: Path,
    subject_ids: List[str],
    config: Config
) -> List[Dict[str, Any]]:
    """
    Run preprocessing for a list of subjects.

    Args:
        raw_dir: Path to raw data.
        processed_dir: Path to save processed data.
        subject_ids: List of subject IDs.
        config: Configuration object.

    Returns:
        List of results dictionaries.
    """
    results = []
    for sub_id in subject_ids:
        res = preprocess_subject(sub_id, raw_dir, processed_dir, config)
        if res:
            results.append(res)

    return results


def main():
    """Main entry point for the preprocessing script."""
    setup_logging()
    config = Config()

    raw_dir = Path(config.raw_data_dir)
    processed_dir = Path(config.processed_data_dir)

    # Placeholder subject list
    subject_ids = [f"sub-{i:03d}" for i in range(1, 11)]

    run_preprocessing(raw_dir, processed_dir, subject_ids, config)


if __name__ == "__main__":
    main()