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
from src.integrity import update_hashes
from src.exceptions import DataUnavailableError, InsufficientSubjectsError
from src.utils import get_logger

logger = get_logger(__name__)

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
    # Check if pre-computed framewise_displacement column exists (FR-002)
    if 'framewise_displacement' in confounds_df.columns:
        fd_values = confounds_df['framewise_displacement'].dropna().values
        if len(fd_values) > 0:
            mean_fd = np.mean(fd_values)
            logger.info(f"Using pre-computed framewise_displacement column. Mean FD: {mean_fd:.4f} mm")
            return float(mean_fd)
    
    # Identify motion parameters (trans_x, trans_y, trans_z, rot_x, rot_y, rot_z)
    # BIDS standard names might vary slightly, check for common patterns
    trans_cols = [c for c in confounds_df.columns if 'trans_x' in c or 'trans_y' in c or 'trans_z' in c]
    rot_cols = [c for c in confounds_df.columns if 'rot_x' in c or 'rot_y' in c or 'rot_z' in c]
    
    if not trans_cols or not rot_cols:
        # Try alternative naming conventions
        trans_cols = [c for c in confounds_df.columns if c.startswith('trans_')]
        rot_cols = [c for c in confounds_df.columns if c.startswith('rot_')]
    
    if not trans_cols or not rot_cols:
        logger.warning(f"Could not find standard motion parameters in {list(confounds_df.columns)}. Attempting fallback.")
        # Fallback: look for 'motion' or 'param' columns
        all_cols = confounds_df.columns
        trans_cols = [c for c in all_cols if 'x' in c and ('trans' in c or 'x' in c)]
        rot_cols = [c for c in all_cols if 'rot' in c]
        
        if not trans_cols or not rot_cols:
            raise DataUnavailableError("Could not identify motion parameters for FD calculation.")

    # Sort columns to ensure consistent order (x, y, z)
    trans_cols.sort(key=lambda x: x[-1])
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

def verify_conditions(subject_id: str, raw_dir: Path) -> Tuple[bool, List[str]]:
    """
    Verify that the subject's events.tsv contains both 'Inclusion' and 'Exclusion' trial types.
    
    Args:
        subject_id: Subject identifier
        raw_dir: Path to raw data directory
        
    Returns:
        Tuple of (is_valid, list of valid conditions)
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
    
    valid_conditions = []
    if has_inclusion:
        valid_conditions.append("Inclusion")
    if has_exclusion:
        valid_conditions.append("Exclusion")
    
    is_valid = has_inclusion and has_exclusion
    return is_valid, valid_conditions

def calculate_subject_motion_metrics_with_conditions(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Calculate motion metrics and verify conditions for all subjects in the raw directory.
    
    Args:
        raw_dir: Path to raw data directory
        
    Returns:
        List of dictionaries with subject metadata
    """
    subjects = [d.name for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith('sub-')]
    
    results = []
    for subj in subjects:
        try:
            motion_metric = calculate_subject_motion_metrics(subj, raw_dir)
            is_valid, valid_conditions = verify_conditions(subj, raw_dir)
            results.append({
                "subject_id": subj,
                "motion_mean": motion_metric,
                "condition_valid": is_valid,
                "conditions": valid_conditions
            })
        except DataUnavailableError as e:
            logger.error(f"Skipping {subj}: {e}")
            results.append({
                "subject_id": subj,
                "motion_mean": None,
                "condition_valid": False,
                "conditions": []
            })
    
    return results

def filter_by_motion_threshold(subject_list: List[Dict[str, Any]], threshold: float = 0.2) -> List[Dict[str, Any]]:
    """
    Filter subjects based on motion threshold and condition validity (FR-002).
    
    Args:
        subject_list: List of subject dictionaries
        threshold: Motion threshold in mm (default 0.2 per FR-002)
        
    Returns:
        Filtered list of subjects with 'qc_status' set
    """
    filtered = []
    for subj in subject_list:
        if subj["motion_mean"] is None:
            subj["qc_status"] = "failed"
            filtered.append(subj)
            continue
        
        # FR-002: exclude if mean FD > 0.2 mm
        is_motion_ok = subj["motion_mean"] <= threshold
        is_condition_ok = subj["condition_valid"]
        
        if is_motion_ok and is_condition_ok:
            subj["qc_status"] = "passed"
        else:
            subj["qc_status"] = "failed"
        
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
    retained_count = sum(1 for s in subject_list if s.get("qc_status") == "passed")
    if retained_count < min_count:
        raise InsufficientSubjectsError(retained_count)

def run_qc_pipeline(raw_dir: str, output_dir: str, motion_threshold: float = 0.2) -> None:
    """
    Run the full QC pipeline: calculate metrics, verify conditions, filter, and save results.
    
    Args:
        raw_dir: Path to raw data directory
        output_dir: Path to output directory for JSON files
        motion_threshold: Motion threshold in mm (default 0.2 per FR-002)
    """
    raw_path = Path(raw_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting QC pipeline for {raw_path}")
    logger.info(f"Motion threshold: {motion_threshold} mm (FR-002)")
    
    # 1. Calculate metrics and verify conditions for all subjects
    all_subjects = calculate_subject_motion_metrics_with_conditions(raw_path)
    
    # 2. Filter by motion threshold (FR-002: 0.2 mm)
    filtered_subjects = filter_by_motion_threshold(all_subjects, threshold=motion_threshold)
    
    # 3. Write full QC list (all subjects with their status)
    full_list_path = output_path / "subject_qc_list.json"
    with open(full_list_path, 'w') as f:
        json.dump(filtered_subjects, f, indent=2)
    logger.info(f"Wrote full QC list to {full_list_path}")
    
    # 4. Write retained subjects list (schema: contracts/subject.schema.yaml)
    retained_list = [s for s in filtered_subjects if s.get("qc_status") == "passed"]
    retained_path = output_path / "subjects_metadata.json"
    with open(retained_path, 'w') as f:
        json.dump(retained_list, f, indent=2)
    logger.info(f"Wrote retained subjects to {retained_path} (N={len(retained_list)})")
    
    # 5. Update integrity hashes
    update_hashes([str(full_list_path), str(retained_path)])
    
    # 6. Check subject count (FR-009)
    try:
        check_subject_count(filtered_subjects, min_count=10)
        logger.info(f"Subject count check passed: {len(retained_list)} subjects retained.")
    except InsufficientSubjectsError as e:
        logger.error(str(e))
        raise

def main():
    """Entry point for QC pipeline execution."""
    config = load_config()
    raw_dir = config.get("paths", {}).get("raw", "data/raw")
    output_dir = config.get("paths", {}).get("processed", "data/processed")
    motion_threshold = 0.2  # FR-002: 0.2 mm threshold
    
    try:
        run_qc_pipeline(raw_dir, output_dir, motion_threshold=motion_threshold)
    except (DataUnavailableError, InsufficientSubjectsError) as e:
        logger.error(f"QC Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
