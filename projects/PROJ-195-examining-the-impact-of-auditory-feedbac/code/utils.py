"""
Utility functions for BIDS path handling, QC logging, and motion threshold checks.

This module provides helpers for:
- Constructing BIDS-compliant file paths
- Logging QC metrics (motion, etc.)
- Filtering subjects based on motion thresholds (>2mm exclusion)
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import re
import json

# Configure logging for the module
logger = logging.getLogger(__name__)


def get_bids_subject_path(root: Path, subject_id: str) -> Path:
    """
    Construct the path to a subject's BIDS directory.

    Args:
        root: Root directory of the BIDS dataset.
        subject_id: Subject identifier (e.g., 'sub-01').

    Returns:
        Path to the subject directory.
    """
    return root / subject_id


def get_bids_func_file(
    subject_path: Path,
    session_id: Optional[str] = None,
    task: str = "main",
    suffix: str = "bold"
) -> Path:
    """
    Construct the path to a functional MRI file for a subject.

    Args:
        subject_path: Path to the subject's BIDS directory.
        session_id: Optional session identifier (e.g., 'ses-01').
        task: Task label (default: 'main').
        suffix: File suffix (default: 'bold').

    Returns:
        Path to the functional file (glob pattern).
    """
    bids_root = subject_path.parent
    if session_id:
        ses_dir = subject_path / session_id
        func_dir = ses_dir / "func"
    else:
        func_dir = subject_path / "func"

    filename_pattern = f"{subject_path.name}_{session_id}_task-{task}_*_{suffix}.nii.gz" if session_id else f"{subject_path.name}_task-{task}_*_{suffix}.nii.gz"
    
    # Return the glob pattern or first match if exists
    glob_pattern = func_dir / filename_pattern
    matches = list(glob_pattern.parent.glob(filename_pattern))
    if matches:
        return matches[0]
    return glob_pattern


def get_fmriprep_output_path(
    bids_root: Path,
    subject_id: str,
    session_id: Optional[str] = None,
    output_dir: str = "derivatives/fmriprep"
) -> Path:
    """
    Construct the path to fmriprep output for a subject.

    Args:
        bids_root: Root directory of the BIDS dataset.
        subject_id: Subject identifier.
        session_id: Optional session identifier.
        output_dir: Relative path to fmriprep output directory.

    Returns:
        Path to the subject's fmriprep output directory.
    """
    if session_id:
        return (
            bids_root / output_dir / subject_id / session_id / "func"
        )
    return (
        bids_root / output_dir / subject_id / "func"
    )


def get_motion_file(fmriprep_output_path: Path) -> Path:
    """
    Get the path to the motion parameters file from fmriprep output.

    Args:
        fmriprep_output_path: Path to the subject's fmriprep func directory.

    Returns:
        Path to the motion parameters file.
    """
    # fmriprep typically outputs: sub-XX_ses-YY_desc-confounds_timeseries.tsv
    # or sub-XX_desc-confounds_timeseries.tsv
    pattern = "*confounds*.tsv"
    files = list(fmriprep_output_path.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No motion parameters file found in {fmriprep_output_path}")
    return files[0]


def parse_motion_parameters(motion_file: Path) -> Dict[str, List[float]]:
    """
    Parse motion parameters from fmriprep confounds file.

    Args:
        motion_file: Path to the confounds TSV file.

    Returns:
        Dictionary with motion parameter columns (trans_x, trans_y, trans_z, 
        rot_x, rot_y, rot_z) and their values.
    """
    import pandas as pd

    df = pd.read_csv(motion_file, sep='\t')
    
    # fmriprep uses specific column names for motion parameters
    motion_cols = [
        'trans_x', 'trans_y', 'trans_z',
        'rot_x', 'rot_y', 'rot_z'
    ]
    
    # Filter to only existing columns
    available_cols = [col for col in motion_cols if col in df.columns]
    
    if not available_cols:
        logger.warning(f"No standard motion columns found in {motion_file}. Available: {list(df.columns)[:10]}")
        return {}
    
    return {col: df[col].tolist() for col in available_cols}


def calculate_frame_displacement(motion_params: Dict[str, List[float]]) -> List[float]:
    """
    Calculate frame-wise displacement from motion parameters.

    Uses the formula: sqrt(sum(trans_diffs^2) + sum(rot_diffs^2 * 50^2))
    where 50mm is a typical head radius approximation.

    Args:
        motion_params: Dictionary with motion parameter lists.

    Returns:
        List of frame-wise displacement values (first value is 0).
    """
    if not motion_params:
        return []
    
    trans_cols = ['trans_x', 'trans_y', 'trans_z']
    rot_cols = ['rot_x', 'rot_y', 'rot_z']
    
    # Get available columns
    trans_data = [motion_params.get(col, []) for col in trans_cols if col in motion_params]
    rot_data = [motion_params.get(col, []) for col in rot_cols if col in motion_params]
    
    if not trans_data and not rot_data:
        return []
    
    # Pad to same length if needed
    max_len = max(len(col) for col in trans_data + rot_data)
    for col_list in trans_data + rot_data:
        while len(col_list) < max_len:
            col_list.append(0.0)
    
    # Calculate differences
    trans_diffs = []
    rot_diffs = []
    
    for i in range(1, max_len):
        trans_diff = sum((col[i] - col[i-1])**2 for col in trans_data)
        rot_diff = sum((col[i] - col[i-1])**2 for col in rot_data)
        
        # Convert rotation from radians to mm (approximate with 50mm radius)
        ffd = (trans_diff + rot_diff * (50.0**2)) ** 0.5
        trans_diffs.append(ffd)
    
    # First frame has no previous frame, so displacement is 0
    return [0.0] + trans_diffs


def check_motion_threshold(
    motion_file: Path,
    threshold_mm: float = 2.0
) -> Tuple[bool, float, List[int]]:
    """
    Check if a subject exceeds the motion threshold.

    Args:
        motion_file: Path to the motion parameters file.
        threshold_mm: Maximum allowed displacement in mm (default: 2.0).

    Returns:
        Tuple of (passes_threshold, max_displacement, list_of_excessive_frames).
        passes_threshold is True if max displacement <= threshold.
    """
    motion_params = parse_motion_parameters(motion_file)
    if not motion_params:
        logger.warning(f"Could not parse motion parameters from {motion_file}")
        return False, float('inf'), []
    
    ffd = calculate_frame_displacement(motion_params)
    max_disp = max(ffd) if ffd else 0.0
    excessive_frames = [i for i, val in enumerate(ffd) if val > threshold_mm]
    
    passes = max_disp <= threshold_mm
    return passes, max_disp, excessive_frames


def log_qc_metrics(
    subject_id: str,
    motion_file: Path,
    threshold_mm: float = 2.0,
    log_file: Optional[Path] = None
) -> Dict:
    """
    Calculate and log QC metrics for a subject.

    Args:
        subject_id: Subject identifier.
        motion_file: Path to motion parameters file.
        threshold_mm: Motion threshold in mm.
        log_file: Optional path to QC log file.

    Returns:
        Dictionary with QC metrics.
    """
    passes, max_disp, excessive_frames = check_motion_threshold(motion_file, threshold_mm)
    
    qc_metrics = {
        'subject_id': subject_id,
        'max_displacement_mm': max_disp,
        'passes_threshold': passes,
        'threshold_mm': threshold_mm,
        'num_excessive_frames': len(excessive_frames),
        'excessive_frames': excessive_frames,
        'motion_file': str(motion_file)
    }
    
    # Log to file if provided
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists to determine header
        file_exists = log_file.exists()
        
        with open(log_file, 'a') as f:
            if not file_exists:
                # Write header
                f.write("subject_id,max_displacement_mm,passes_threshold,threshold_mm,num_excessive_frames\n")
            
            f.write(f"{subject_id},{max_disp:.4f},{passes},{threshold_mm},{len(excessive_frames)}\n")
        
        logger.info(f"QC metrics logged for {subject_id}: max_disp={max_disp:.4f}mm, passes={passes}")
    
    return qc_metrics


def filter_subjects_by_motion(
    bids_root: Path,
    output_file: Path,
    output_dir: str = "derivatives/fmriprep",
    threshold_mm: float = 2.0,
    qc_log_file: Optional[Path] = None
) -> List[str]:
    """
    Filter subjects based on motion threshold and generate a list of valid subjects.

    Args:
        bids_root: Root directory of the BIDS dataset.
        output_file: Path to write the list of valid subjects.
        output_dir: Relative path to fmriprep output directory.
        threshold_mm: Motion threshold in mm (default: 2.0).
        qc_log_file: Optional path to QC log file.

    Returns:
        List of subject IDs that pass the motion threshold.
    """
    # Find all subjects
    subjects = [d.name for d in bids_root.iterdir() if d.is_dir() and d.name.startswith('sub-')]
    
    valid_subjects = []
    
    for subject_id in sorted(subjects):
        try:
            # Determine session (if any)
            subject_path = bids_root / subject_id
            session_id = None
            
            # Check for session subdirectory
            sessions = [d.name for d in subject_path.iterdir() if d.is_dir() and d.name.startswith('ses-')]
            if sessions:
                session_id = sessions[0]
            
            # Get fmriprep output path
            fmriprep_path = get_fmriprep_output_path(bids_root, subject_id, session_id, output_dir)
            
            # Get motion file
            motion_file = get_motion_file(fmriprep_path)
            
            # Check motion
            passes, max_disp, _ = check_motion_threshold(motion_file, threshold_mm)
            
            if passes:
                valid_subjects.append(subject_id)
                logger.info(f"{subject_id}: PASS (max_disp={max_disp:.4f}mm)")
            else:
                logger.warning(f"{subject_id}: EXCLUDED (max_disp={max_disp:.4f}mm > {threshold_mm}mm)")
            
            # Log QC metrics
            if qc_log_file:
                log_qc_metrics(subject_id, motion_file, threshold_mm, qc_log_file)
                
        except FileNotFoundError as e:
            logger.error(f"Error processing {subject_id}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing {subject_id}: {e}")
            continue
    
    # Write valid subjects to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        for subject_id in valid_subjects:
            f.write(f"{subject_id}\n")
    
    logger.info(f"Filtered {len(valid_subjects)}/{len(subjects)} subjects. Valid subjects saved to {output_file}")
    
    return valid_subjects


def get_event_file_path(
    bids_root: Path,
    subject_id: str,
    task: str = "main",
    session_id: Optional[str] = None
) -> Path:
    """
    Get the path to the events TSV file for a subject.

    Args:
        bids_root: Root directory of the BIDS dataset.
        subject_id: Subject identifier.
        task: Task label.
        session_id: Optional session identifier.

    Returns:
        Path to the events file.
    """
    subject_path = bids_root / subject_id
    if session_id:
        func_dir = subject_path / session_id / "func"
    else:
        func_dir = subject_path / "func"
    
    filename = f"{subject_id}"
    if session_id:
        filename += f"_{session_id}"
    filename += f"_task-{task}_events.tsv"
    
    return func_dir / filename