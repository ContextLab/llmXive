"""
Error handling infrastructure for the Narrative Archaeology pipeline.

This module provides utilities to:
1. Calculate motion metrics from fMRIPrep outputs.
2. Check subjects against motion thresholds.
3. Log errors in a structured JSON format to data/errors.log.
4. Handle subject-level errors gracefully (skip and log).
"""
import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd

# Import config to access thresholds and paths
import code.config as config

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def calculate_motion_metrics(subject_id: str, preproc_dir: Path) -> Dict[str, float]:
    """
    Calculate motion metrics (FD and DVARS) for a subject.

    This function attempts to read the 'confounds_regressors.tsv' file generated
    by fMRIPrep (or nilearn preprocessing) to compute Framewise Displacement (FD)
    and DVARS.

    Args:
        subject_id: The subject identifier (e.g., 'sub-01').
        preproc_dir: Path to the subject's preprocessed directory.

    Returns:
        A dictionary containing:
            - 'mean_fd': Mean Framewise Displacement (mm).
            - 'max_fd': Maximum Framewise Displacement (mm).
            - 'mean_dvars': Mean DVARS.
            - 'pct_high_fd': Percentage of timepoints with FD > 0.5mm.

    Raises:
        FileNotFoundError: If the confounds file is not found.
        ValueError: If the required columns are missing.
    """
    confounds_file = preproc_dir / f"{subject_id}_desc-confounds_regressors.tsv"
    
    if not confounds_file.exists():
        # Fallback to common nilearn/nipype naming if standard fmriprep name is missing
        # Look for any tsv with 'confounds' in the name in the directory
        candidates = list(preproc_dir.glob("*confounds*.tsv"))
        if candidates:
            confounds_file = candidates[0]
        else:
            raise FileNotFoundError(f"Confounds file not found for {subject_id} in {preproc_dir}")

    logger.info(f"Reading confounds from {confounds_file}")
    try:
        confounds = pd.read_csv(confounds_file, sep='\t', low_memory=False)
    except Exception as e:
        raise ValueError(f"Failed to parse confounds file for {subject_id}: {e}")

    # Check for required columns
    # Standard fmriprep: 'trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z'
    # Or 'framewise_displacement' directly if pre-calculated
    
    metrics = {
        'mean_fd': 0.0,
        'max_fd': 0.0,
        'mean_dvars': 0.0,
        'pct_high_fd': 0.0,
        'raw_fd_values': []
    }

    # Calculate FD if not present
    if 'framewise_displacement' in confounds.columns:
        fd_series = confounds['framewise_displacement'].dropna()
    else:
        # Calculate FD from displacement and rotation
        required_trans = ['trans_x', 'trans_y', 'trans_z']
        required_rot = ['rot_x', 'rot_y', 'rot_z']
        
        if not all(col in confounds.columns for col in required_trans + required_rot):
            # Try alternative column names sometimes used
            available_cols = confounds.columns.tolist()
            if not all(col in available_cols for col in required_trans):
                raise ValueError(f"Missing translation columns. Found: {available_cols}")
            if not all(col in available_cols for col in required_rot):
                raise ValueError(f"Missing rotation columns. Found: {available_cols}")

        trans = confounds[required_trans].values
        rot = confounds[required_rot].values

        # FD = sum of absolute differences in translation (mm) + sum of absolute differences in rotation (mm)
        # Rotation is in radians; convert to mm assuming 50mm radius (standard convention)
        radius = 50.0
        
        diff_trans = np.abs(np.diff(trans, axis=0))
        diff_rot = np.abs(np.diff(rot, axis=0))
        
        fd = np.sum(diff_trans, axis=1) + radius * np.sum(diff_rot, axis=1)
        fd_series = pd.Series(fd)

    # Handle potential NaNs in FD
    fd_series = fd_series.dropna()
    
    if len(fd_series) == 0:
        logger.warning(f"No valid FD values found for {subject_id}")
        return metrics

    metrics['mean_fd'] = float(fd_series.mean())
    metrics['max_fd'] = float(fd_series.max())
    metrics['raw_fd_values'] = fd_series.tolist()
    
    # Calculate percentage of high motion timepoints
    high_motion_threshold = config.MOTION_THRESHOLD_MM
    if high_motion_threshold is None:
        high_motion_threshold = 0.5 # Default fallback if config missing
        
    pct_high = (fd_series > high_motion_threshold).mean() * 100
    metrics['pct_high_fd'] = float(pct_high)

    # DVARS calculation if available
    if 'dvars' in confounds.columns:
        dvars_series = confounds['dvars'].dropna()
        if len(dvars_series) > 0:
            metrics['mean_dvars'] = float(dvars_series.mean())

    return metrics


def check_motion_artifacts(metrics: Dict[str, float], threshold_mm: Optional[float] = None) -> bool:
    """
    Determine if a subject should be skipped based on motion metrics.

    Args:
        metrics: Dictionary returned by calculate_motion_metrics.
        threshold_mm: Motion threshold in mm (defaults to config.MOTION_THRESHOLD_MM).

    Returns:
        True if the subject has excessive motion and should be SKIPPED.
        False if the subject is acceptable.
    """
    if threshold_mm is None:
        threshold_mm = config.MOTION_THRESHOLD_MM
        if threshold_mm is None:
            threshold_mm = 0.5 # Default safety threshold

    mean_fd = metrics.get('mean_fd', 0.0)
    pct_high = metrics.get('pct_high_fd', 0.0)

    # Skip if mean FD exceeds threshold
    if mean_fd > threshold_mm:
        logger.warning(f"Motion check failed (mean FD): {mean_fd:.4f} > {threshold_mm}")
        return True

    # Skip if > 20% of timepoints have high motion
    if pct_high > 20.0:
        logger.warning(f"Motion check failed (pct high FD): {pct_high:.1f}% > 20%")
        return True

    return False


def log_error(subject_id: str, error_code: str, error_message: str, motion_mm: float = 0.0) -> None:
    """
    Log an error to the data/errors.log file in JSON format.

    Args:
        subject_id: The subject identifier.
        error_code: A short code (e.g., 'MOTION_ARTIFACT', 'FILE_NOT_FOUND').
        error_message: Detailed description of the error.
        motion_mm: The mean FD value associated with the error (if applicable).
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "subject_id": subject_id,
        "error_code": error_code,
        "error_message": error_message,
        "motion_mm": motion_mm
    }

    # Ensure data directory exists
    data_dir = Path(config.DATA_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = data_dir / "errors.log"

    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        logger.info(f"Error logged for {subject_id}: {error_code}")
    except Exception as e:
        logger.error(f"Failed to write to error log: {e}")


def handle_subject_error(subject_id: str, error_code: str, error_message: str, motion_mm: float = 0.0) -> None:
    """
    Centralized handler for subject-level errors.
    
    This function logs the error and raises a specific exception to signal
    the calling pipeline to skip the subject.

    Args:
        subject_id: The subject identifier.
        error_code: A short code.
        error_message: Detailed description.
        motion_mm: Motion metric value.
    """
    log_error(subject_id, error_code, error_message, motion_mm)
    raise RuntimeError(f"Skipping subject {subject_id} due to {error_code}: {error_message}")


def get_error_summary(log_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Read the error log and return a summary of errors.

    Args:
        log_file: Path to errors.log. Defaults to config.DATA_DIR/errors.log.

    Returns:
        Dictionary with counts per error_code and total errors.
    """
    if log_file is None:
        log_file = Path(config.DATA_DIR) / "errors.log"

    if not log_file.exists():
        return {"total_errors": 0, "by_code": {}}

    errors = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    errors.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    summary = {
        "total_errors": len(errors),
        "by_code": {}
    }

    for err in errors:
        code = err.get('error_code', 'UNKNOWN')
        summary['by_code'][code] = summary['by_code'].get(code, 0) + 1

    return summary


def clear_error_log(log_file: Optional[Path] = None) -> None:
    """
    Clear the error log file. Use with caution.

    Args:
        log_file: Path to errors.log. Defaults to config.DATA_DIR/errors.log.
    """
    if log_file is None:
        log_file = Path(config.DATA_DIR) / "errors.log"

    if log_file.exists():
        log_file.unlink()
        logger.info("Error log cleared.")
    else:
        logger.info("Error log does not exist, nothing to clear.")
