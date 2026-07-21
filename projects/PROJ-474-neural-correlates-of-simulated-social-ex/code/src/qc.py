"""
Quality Control (QC) module for fMRI data processing.
Handles motion calculation, condition verification, and subject filtering.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.config import load_config
from src.integrity import update_hashes, get_logger as get_integrity_logger
from src.exceptions import DataUnavailableError, InsufficientSubjectsError

# Configure logger for this module
logger = logging.getLogger(__name__)

def load_motion_parameters(subject_id: str, raw_dir: Path) -> pd.DataFrame:
    """
    Load motion parameters from the confounds TSV file for a given subject.
    
    Args:
        subject_id: The subject identifier (e.g., 'sub-01')
        raw_dir: Path to the raw data directory (BIDS root)
        
    Returns:
        DataFrame containing motion parameters
        
    Raises:
        DataUnavailableError: If confounds file is not found
    """
    # BIDS pattern for confounds
    confounds_pattern = raw_dir / subject_id / "func" / f"{subject_id}_task-cyberball_run-*_desc-confounds_timeseries.tsv"
    
    # Find the first matching file
    confounds_files = list(confounds_pattern.parent.glob(f"{subject_id}_task-cyberball_run-*_desc-confounds_timeseries.tsv"))
    
    if not confounds_files:
        # Fallback for simpler BIDS structures if run number varies
        confounds_files = list((raw_dir / subject_id / "func").glob(f"{subject_id}_*_desc-confounds_timeseries.tsv"))
        
    if not confounds_files:
        raise DataUnavailableError(f"Confounds file not found for subject {subject_id} in {raw_dir}")
    
    # Use the first found file
    confounds_file = confounds_files[0]
    logger.info(f"Loading confounds from: {confounds_file}")
    
    try:
        df = pd.read_csv(confounds_file, sep='\t')
    except Exception as e:
        raise DataUnavailableError(f"Failed to read confounds file {confounds_file}: {str(e)}")
    
    return df

def calculate_framewise_displacement(confounds_df: pd.DataFrame) -> float:
    """
    Calculate Framewise Displacement (FD) from motion parameters.
    
    Uses the standard Jenkinson FD formula:
    FD = |Δx| + |Δy| + |Δz| + |Δα| + |Δβ| + |Δγ|
    where Δ represents the absolute difference of the motion parameter from the previous volume.
    Rotations are converted to mm assuming a radius of 50mm.
    
    Args:
        confounds_df: DataFrame containing motion parameters
        
    Returns:
        Mean Framewise Displacement (float)
    """
    # Identify motion parameters (trans_x, trans_y, trans_z, rot_x, rot_y, rot_z)
    # BIDS standard names might vary slightly, check for common patterns
    motion_cols = []
    trans_cols = [c for c in confounds_df.columns if 'trans_x' in c or 'trans_y' in c or 'trans_z' in c]
    rot_cols = [c for c in confounds_df.columns if 'rot_x' in c or 'rot_y' in c or 'rot_z' in c]
    
    if not trans_cols or not rot_cols:
        # Try alternative naming conventions (e.g., 'trans_x', 'rot_x' without 'trans_' prefix in some versions)
        trans_cols = [c for c in confounds_df.columns if c.startswith('trans_')]
        rot_cols = [c for c in confounds_df.columns if c.startswith('rot_')]
    
    if not trans_cols or not rot_cols:
        logger.warning(f"Could not find standard motion parameters in {confounds_df.columns}. Attempting fallback.")
        # Fallback: look for 'motion' or 'param' columns
        all_cols = confounds_df.columns
        trans_cols = [c for c in all_cols if 'x' in c and ('trans' in c or 'x' in c)]
        rot_cols = [c for c in all_cols if 'rot' in c]
        
        if not trans_cols or not rot_cols:
            raise DataUnavailableError("Could not identify motion parameters for FD calculation.")

    # Sort columns to ensure consistent order (x, y, z)
    trans_cols.sort(key=lambda x: x[-1]) # Sort by last char (x, y, z)
    rot_cols.sort(key=lambda x: x[-1])

    motion_params = confounds_df[trans_cols + rot_cols].values
    
    # Calculate absolute differences between consecutive volumes
    diff = np.abs(np.diff(motion_params, axis=0))
    
    # Convert rotation to mm (radius = 50mm)
    # Rotation values are typically in radians
    rotation_radius = 50.0
    fd_values = diff[:, 0:3].sum(axis=1) + (diff[:, 3:6] * rotation_radius).sum(axis=1)
    
    # Mean FD (excluding the first volume which has no previous)
    mean_fd = np.mean(fd_values)
    
    return float(mean_fd)

def calculate_subject_motion_metrics(subject_id: str, raw_dir: Path) -> float:
    """
    Calculate the motion metric (FD) for a specific subject.
    
    Args:
        subject_id: Subject identifier
        raw_dir: Path to raw data directory
        
    Returns:
        Mean FD value (float)
    """
    confounds_df = load_motion_parameters(subject_id, raw_dir)
    fd = calculate_framewise_displacement(confounds_df)
    logger.info(f"Subject {subject_id} mean FD: {fd:.4f} mm")
    return fd

def verify_conditions(subject_id: str, raw_dir: Path) -> Tuple[bool, str]:
    """
    Verify that the subject's events.tsv contains both 'Inclusion' and 'Exclusion' trial types.
    
    Args:
        subject_id: Subject identifier
        raw_dir: Path to raw data directory
        
    Returns:
        Tuple of (is_valid, status_message)
    """
    events_pattern = raw_dir / subject_id / "func" / f"{subject_id}_task-cyberball_run-*_events.tsv"
    events_files = list(events_pattern.parent.glob(f"{subject_id}_task-cyberball_run-*_events.tsv"))
    
    if not events_files:
        events_files = list((raw_dir / subject_id / "func").glob(f"{subject_id}_*_events.tsv"))
        
    if not events_files:
        raise DataUnavailableError(f"Events file not found for subject {subject_id}")
    
    events_file = events_files[0]
    try:
        events_df = pd.read_csv(events_file, sep='\t')
    except Exception as e:
        raise DataUnavailableError(f"Failed to read events file {events_file}: {str(e)}")
    
    if 'trial_type' not in events_df.columns:
        raise DataUnavailableError(f"'trial_type' column missing in {events_file}")
    
    trial_types = set(events_df['trial_type'].astype(str).str.strip().unique())
    
    has_inclusion = any('Inclusion' in t for t in trial_types)
    has_exclusion = any('Exclusion' in t for t in trial_types)
    
    if has_inclusion and has_exclusion:
        return True, "valid"
    elif not has_inclusion and not has_exclusion:
        return False, "invalid (missing both)"
    elif not has_inclusion:
        return False, "invalid (missing Inclusion)"
    else:
        return False, "invalid (missing Exclusion)"

def calculate_subject_motion_metrics_with_conditions(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Calculate motion metrics and verify conditions for all subjects in the raw directory.
    
    Args:
        raw_dir: Path to raw data directory
        
    Returns:
        List of dictionaries with subject metadata
    """
    config = load_config()
    subjects = [d.name for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith('sub-')]
    
    results = []
    for subj in subjects:
        try:
            motion_metric = calculate_subject_motion_metrics(subj, raw_dir)
            is_valid, status = verify_conditions(subj, raw_dir)
            results.append({
                "subject_id": subj,
                "motion_metric": motion_metric,
                "condition_status": status,
                "retained": False # Default, will be updated by filter
            })
        except DataUnavailableError as e:
            logger.error(f"Skipping {subj}: {e}")
            results.append({
                "subject_id": subj,
                "motion_metric": None,
                "condition_status": "error",
                "retained": False
            })
    
    return results

def filter_by_motion_threshold(subject_list: List[Dict[str, Any]], threshold: float) -> List[Dict[str, Any]]:
    """
    Filter subjects based on motion threshold and condition validity.
    
    Args:
        subject_list: List of subject dictionaries from calculate_subject_motion_metrics_with_conditions
        threshold: Motion threshold in mm
        
    Returns:
        Filtered list of subjects with 'retained' flag set
    """
    filtered = []
    for subj in subject_list:
        if subj["motion_metric"] is None:
            subj["retained"] = False
            filtered.append(subj)
            continue
            
        is_motion_ok = subj["motion_metric"] <= threshold
        is_condition_ok = subj["condition_status"] == "valid"
        
        subj["retained"] = is_motion_ok and is_condition_ok
        filtered.append(subj)
        
    return filtered

def check_subject_count(subject_list: List[Dict[str, Any]], min_count: int = 10) -> None:
    """
    Check if the number of retained subjects meets the minimum requirement.
    
    Args:
        subject_list: List of subject dictionaries
        min_count: Minimum required subjects
        
    Raises:
        InsufficientSubjectsError: If retained count < min_count
    """
    retained_count = sum(1 for s in subject_list if s.get("retained", False))
    if retained_count < min_count:
        raise InsufficientSubjectsError(retained_count)

def run_qc_pipeline(raw_dir: str, output_dir: str) -> None:
    """
    Run the full QC pipeline: calculate metrics, verify conditions, filter, and save results.
    
    Args:
        raw_dir: Path to raw data directory
        output_dir: Path to output directory for JSON files
    """
    raw_path = Path(raw_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting QC pipeline for {raw_path}")
    
    # 1. Calculate metrics and verify conditions for all subjects
    full_list = calculate_subject_motion_metrics_with_conditions(raw_path)
    
    # 2. Filter by motion threshold (from config)
    config = load_config()
    threshold = config.get("motion_threshold", 3.0)
    filtered_list = filter_by_motion_threshold(full_list, threshold)
    
    # 3. Write full list (including excluded)
    full_list_path = output_path / "subject_qc_list.json"
    with open(full_list_path, 'w') as f:
        json.dump(full_list, f, indent=2)
    logger.info(f"Wrote full QC list to {full_list_path}")
    
    # 4. Write retained subjects list
    retained_list = [s for s in filtered_list if s.get("retained", False)]
    retained_path = output_path / "subjects_metadata.json"
    with open(retained_path, 'w') as f:
        json.dump(retained_list, f, indent=2)
    logger.info(f"Wrote retained subjects to {retained_path} (N={len(retained_list)})")
    
    # 5. Update integrity hashes
    update_hashes([str(full_list_path), str(retained_path)])
    
    # 6. Check subject count
    try:
        check_subject_count(filtered_list, min_count=config.get("min_subjects", 10))
        logger.info(f"Subject count check passed: {len(retained_list)} subjects retained.")
    except InsufficientSubjectsError as e:
        logger.error(str(e))
        # Re-raise to halt pipeline if necessary
        raise

def main():
    """Entry point for QC pipeline execution."""
    config = load_config()
    raw_dir = config.get("paths", {}).get("raw", "data/raw")
    output_dir = config.get("paths", {}).get("processed", "data/processed")
    
    try:
        run_qc_pipeline(raw_dir, output_dir)
    except (DataUnavailableError, InsufficientSubjectsError) as e:
        logger.error(f"QC Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()