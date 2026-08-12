import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import re
import json
import sys

# Configure logger for the module
logger = logging.getLogger(__name__)

def get_bids_subject_path(root: Path, subject_id: str) -> Path:
    """Construct the path to a subject's BIDS directory."""
    return root / f"sub-{subject_id}"

def get_bids_func_file(subject_path: Path, session: Optional[str] = None) -> Path:
    """Construct the path to the functional nifti file for a subject."""
    suffix = "task-motor"
    if session:
        return subject_path / "func" / f"{subject_path.name}_{session}_{suffix}_bold.nii.gz"
    return subject_path / "func" / f"{subject_path.name}_{suffix}_bold.nii.gz"

def get_fmriprep_output_path(root: Path, subject_id: str, session: Optional[str] = None) -> Path:
    """Get the fmriprep derivatives path for a subject."""
    sub_dir = f"sub-{subject_id}"
    if session:
        sub_dir += f"/{session}"
    return root / "derivatives" / "fmriprep" / sub_dir / "func"

def get_motion_file(fmriprep_out: Path, subject_id: str, session: Optional[str] = None) -> Path:
    """Get the path to the confounds_regressors.tsv file."""
    sub_prefix = f"sub-{subject_id}"
    if session:
        sub_prefix += f"_{session}"
    return fmriprep_out / f"{sub_prefix}_task-motor_desc-confounds_timeseries.tsv"

def parse_motion_parameters(confounds_path: Path) -> List[Tuple[float, ...]]:
    """
    Parse the confounds TSV file and extract motion parameters (rotations and translations).
    Returns a list of tuples (rot_x, rot_y, rot_z, trans_x, trans_y, trans_z).
    """
    if not confounds_path.exists():
        raise FileNotFoundError(f"Confounds file not found: {confounds_path}")

    params = []
    with open(confounds_path, 'r') as f:
        lines = f.readlines()

    if not lines:
        return []

    # Parse header to find motion columns
    header = lines[0].strip().split('\t')
    motion_cols = [
        'rot_x', 'rot_y', 'rot_z',
        'trans_x', 'trans_y', 'trans_z'
    ]
    
    col_indices = []
    for col in motion_cols:
        if col in header:
            col_indices.append(header.index(col))
        else:
            # Fallback for potential naming variations
            idx = next((i for i, h in enumerate(header) if col in h), -1)
            if idx == -1:
                raise ValueError(f"Could not find motion column {col} in {confounds_path}")
            col_indices.append(idx)

    # Parse data rows
    for line in lines[1:]:
        if not line.strip():
            continue
        values = line.strip().split('\t')
        if len(values) < max(col_indices) + 1:
            continue
        try:
            row_vals = tuple(float(values[i]) for i in col_indices)
            params.append(row_vals)
        except ValueError:
            continue

    return params

def calculate_frame_displacement(motion_params: List[Tuple[float, ...]]) -> List[float]:
    """
    Calculate frame-wise displacement (FWD) from motion parameters.
    FWD is the sum of absolute differences of translations and rotations.
    """
    if not motion_params:
        return []

    displacements = []
    for i in range(1, len(motion_params)):
        prev = motion_params[i-1]
        curr = motion_params[i]
        # Translations are in mm, rotations in radians
        # Convert rotations to mm (approximate for 40mm radius)
        rot_factor = 40.0 
        
        dx = abs(curr[3] - prev[3])
        dy = abs(curr[4] - prev[4])
        dz = abs(curr[5] - prev[5])
        
        drx = abs(curr[0] - prev[0]) * rot_factor
        dry = abs(curr[1] - prev[1]) * rot_factor
        drz = abs(curr[2] - prev[2]) * rot_factor

        displacements.append(dx + dy + dz + drx + dry + drz)
    
    return displacements

def check_motion_threshold(displacements: List[float], threshold: float = 2.0) -> bool:
    """
    Check if any frame displacement exceeds the threshold.
    Returns True if motion is acceptable (all < threshold), False otherwise.
    """
    return all(d < threshold for d in displacements)

def log_qc_metrics(subject_id: str, displacements: List[float], threshold: float, log_path: Path):
    """Log QC metrics for a subject to a file."""
    if not log_path.parent.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    max_disp = max(displacements) if displacements else 0.0
    mean_disp = sum(displacements) / len(displacements) if displacements else 0.0
    exceeded = any(d >= threshold for d in displacements)
    
    status = "PASS" if not exceeded else "FAIL"
    
    with open(log_path, 'a') as f:
        f.write(f"{subject_id},{status},{max_disp:.4f},{mean_disp:.4f}\n")

def filter_subjects_by_motion(subjects: List[str], motion_threshold: float = 2.0, 
                              fmriprep_root: Optional[Path] = None) -> List[str]:
    """
    Filter a list of subjects based on motion criteria.
    Returns subjects where max frame displacement < threshold.
    """
    if fmriprep_root is None:
        fmriprep_root = Path("data/derivatives/fmriprep")
    
    valid_subjects = []
    for sub in subjects:
        sub_path = Path(f"sub-{sub}")
        confounds = fmriprep_root / sub_path / "func" / f"{sub_path}_task-motor_desc-confounds_timeseries.tsv"
        
        if not confounds.exists():
            logger.warning(f"Confounds file missing for {sub}, excluding.")
            continue
        
        try:
            params = parse_motion_parameters(confounds)
            displacements = calculate_frame_displacement(params)
            
            if check_motion_threshold(displacements, motion_threshold):
                valid_subjects.append(sub)
            else:
                logger.info(f"Subject {sub} exceeded motion threshold ({motion_threshold}mm). Excluding.")
        except Exception as e:
            logger.error(f"Error processing motion for {sub}: {e}")
            continue
    
    return valid_subjects

def get_event_file_path(bids_root: Path, subject_id: str, session: Optional[str] = None) -> Path:
    """
    Locate the events TSV file for a given subject.
    """
    sub_prefix = f"sub-{subject_id}"
    if session:
        sub_prefix += f"_{session}"
    
    func_dir = bids_root / sub_prefix / "func"
    if not func_dir.exists():
        raise FileNotFoundError(f"Functional directory not found for {subject_id}")
    
    # Look for the events file
    pattern = f"{sub_prefix}_task-motor_events.tsv"
    events_files = list(func_dir.glob(pattern))
    
    if not events_files:
        raise FileNotFoundError(f"No events file found for {subject_id} in {func_dir}")
    
    return events_files[0]

def validate_event_labels(bids_root: Path, subject_id: str, 
                          required_labels: List[str], 
                          session: Optional[str] = None) -> bool:
    """
    Validate that the events file for a subject contains all required condition labels.
    
    Args:
        bids_root: Path to the BIDS dataset root.
        subject_id: The subject identifier (e.g., '01').
        required_labels: List of condition names that must be present (e.g., ['normal', 'delayed', 'pitch-shifted']).
        session: Optional session identifier.
    
    Returns:
        True if all required labels are present.
    
    Raises:
        SystemExit: If any required label is missing, exits with code 1 and logs the error.
    """
    try:
        events_path = get_event_file_path(bids_root, subject_id, session)
    except FileNotFoundError as e:
        logger.error(f"Event file validation failed for {subject_id}: {e}")
        print(f"ERROR: Missing required event labels", file=sys.stderr)
        sys.exit(1)

    try:
        with open(events_path, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            logger.error(f"Events file is empty for {subject_id}")
            print(f"ERROR: Missing required event labels", file=sys.stderr)
            sys.exit(1)
        
        # Parse header to find 'trial_type' or 'condition' column
        header = lines[0].strip().split('\t')
        label_col = None
        for col in ['trial_type', 'condition', 'stim_type']:
            if col in header:
                label_col = col
                break
        
        if label_col is None:
            logger.error(f"Could not find trial_type/condition column in {events_path}")
            print(f"ERROR: Missing required event labels", file=sys.stderr)
            sys.exit(1)
        
        col_idx = header.index(label_col)
        
        # Collect unique labels found in the file
        found_labels = set()
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.strip().split('\t')
            if len(parts) > col_idx:
                val = parts[col_idx].strip()
                if val:
                    found_labels.add(val)
        
        # Check for missing required labels
        missing = set(required_labels) - found_labels
        
        if missing:
            logger.error(f"Subject {subject_id} missing event labels: {missing}")
            print(f"ERROR: Missing required event labels", file=sys.stderr)
            sys.exit(1)
        
        logger.info(f"Subject {subject_id} event validation passed. Found: {found_labels}")
        return True

    except Exception as e:
        logger.error(f"Error validating events for {subject_id}: {e}")
        print(f"ERROR: Missing required event labels", file=sys.stderr)
        sys.exit(1)

def validate_all_subjects_events(bids_root: Path, subjects: List[str], 
                                 required_labels: List[str],
                                 session: Optional[str] = None) -> bool:
    """
    Validate event labels for a list of subjects.
    Returns True if all pass, otherwise exits.
    """
    for sub in subjects:
        validate_event_labels(bids_root, sub, required_labels, session)
    return True