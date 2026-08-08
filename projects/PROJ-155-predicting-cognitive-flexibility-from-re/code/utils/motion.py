import csv
import os
from typing import List, Dict, Tuple, Optional
import numpy as np
import nibabel as nib
from code.config import get_config
from code.utils.logging import log_exclusion, get_exclusion_log_path
from code.data.paths import get_processed_path, ensure_dir

def calculate_mean_fd(motion_params: np.ndarray) -> float:
    """
    Calculates the Mean Framewise Displacement (FD) from motion parameters.
    
    Args:
        motion_params: A numpy array of shape (n_timepoints, 6) containing
                       3 translation (mm) and 3 rotation (rad) parameters.
                        
    Returns:
        float: The mean FD value.
    """
    if motion_params.shape[1] != 6:
        raise ValueError("Motion parameters must have 6 columns (3 trans, 3 rot).")
    
    # Delta between consecutive timepoints
    deltas = np.diff(motion_params, axis=0)
    
    # FD calculation (Power et al., 2012)
    # Translation: sum of absolute differences
    # Rotation: sum of absolute differences * radius (50mm is standard)
    trans_deltas = np.abs(deltas[:, :3]).sum(axis=1)
    rot_deltas = np.abs(deltas[:, 3:]).sum(axis=1) * 50.0
    
    fd = trans_deltas + rot_deltas
    
    return float(np.mean(fd))

def load_motion_params_from_nifti(nifti_path: str) -> np.ndarray:
    """
    Loads motion parameters from a NIfTI file (assuming they are stored in the header or a sidecar).
    
    Note: In the HCP pipeline, motion parameters are often stored in a separate .txt or .mat file.
    This function attempts to extract them if embedded or loads a sidecar if the path implies it.
    For this implementation, we assume the motion parameters are provided as a sidecar .txt
    with the same base name as the NIfTI file.
    
    Args:
        nifti_path: Path to the NIfTI file.
        
    Returns:
        np.ndarray: Array of motion parameters.
    """
    base_path = os.path.splitext(nifti_path)[0]
    txt_path = base_path + ".txt"
    
    if not os.path.exists(txt_path):
        # Fallback: try to load from a standard HCP sidecar name
        txt_path = base_path + "_MovementParameters.txt"
    
    if not os.path.exists(txt_path):
        raise FileNotFoundError(f"Motion parameters file not found for {nifti_path}. Expected: {txt_path}")
    
    data = np.loadtxt(txt_path)
    if data.ndim == 1:
        data = data.reshape(-1, 6)
    return data

def check_motion_exclusion(mean_fd: float, threshold: Optional[float] = None) -> Tuple[bool, str]:
    """
    Checks if a subject should be excluded based on Mean FD.
    
    Args:
        mean_fd: The calculated Mean FD.
        threshold: The FD threshold. Defaults to config value.
        
    Returns:
        Tuple[bool, str]: (Should exclude, Reason).
    """
    if threshold is None:
        config = get_config()
        threshold = config.get("fd_threshold", 0.2)
    
    if mean_fd > threshold:
        return True, f"Mean FD ({mean_fd:.4f}) > threshold ({threshold})"
    return False, ""

def generate_exclusion_log(subjects: List[Dict], log_path: str) -> None:
    """
    Generates the exclusion log CSV.
    
    Args:
        subjects: List of dicts with 'Subject_ID', 'Exclusion_Reason', 'Mean_FD'.
        log_path: Path to save the CSV.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Subject_ID', 'Exclusion_Reason', 'Mean_FD'])
        writer.writeheader()
        writer.writerows(subjects)

def process_subject_motion(nifti_path: str, subject_id: str, threshold: Optional[float] = None) -> Tuple[float, bool, str]:
    """
    Processes motion for a single subject.
    
    Args:
        nifti_path: Path to the NIfTI file.
        subject_id: Subject ID.
        threshold: FD threshold.
        
    Returns:
        Tuple[float, bool, str]: (Mean_FD, Should_Exclude, Reason).
    """
    try:
        params = load_motion_params_from_nifti(nifti_path)
        mean_fd = calculate_mean_fd(params)
        should_exclude, reason = check_motion_exclusion(mean_fd, threshold)
        return mean_fd, should_exclude, reason
    except Exception as e:
        return 0.0, True, f"Error loading motion params: {str(e)}"

def run_motion_filtering_pipeline(subjects_data: List[Dict]) -> List[Dict]:
    """
    Runs the motion filtering pipeline on a list of subject data dictionaries.
    
    This function iterates through the provided subject data, calculates Mean FD for each,
    and filters out subjects exceeding the configured threshold. Excluded subjects are
    logged to `data/processed/exclusion_log.csv`.
    
    Args:
        subjects_data: List of dicts containing 'Subject_ID', 'Nifti_Path', and optionally 'Mean_FD' (if pre-calculated).
        
    Returns:
        List[Dict]: The filtered list of subjects that passed the motion check.
    """
    config = get_config()
    threshold = config.get("fd_threshold", 0.2)
    excluded_subjects = []
    valid_subjects = []
    
    log_path = get_exclusion_log_path()
    
    for subject in subjects_data:
        subject_id = subject['Subject_ID']
        nifti_path = subject.get('Nifti_Path')
        
        # If Mean_FD is already provided (e.g., from T005/T012), use it
        if 'Mean_FD' in subject:
            mean_fd = float(subject['Mean_FD'])
            should_exclude, reason = check_motion_exclusion(mean_fd, threshold)
        elif nifti_path and os.path.exists(nifti_path):
            try:
                mean_fd, should_exclude, reason = process_subject_motion(nifti_path, subject_id, threshold)
            except Exception as e:
                # If we can't calculate FD, we must exclude to be safe, or log error
                mean_fd = 0.0
                should_exclude = True
                reason = f"Error calculating FD: {str(e)}"
        else:
            # Missing data path
            mean_fd = 0.0
            should_exclude = True
            reason = "Missing NIfTI path or file"
        
        if should_exclude:
            excluded_subjects.append({
                'Subject_ID': subject_id,
                'Exclusion_Reason': 'Motion',
                'Mean_FD': f"{mean_fd:.4f}"
            })
            log_exclusion(subject_id, 'Motion', f"{mean_fd:.4f}")
        else:
            valid_subjects.append(subject)
    
    if excluded_subjects:
        generate_exclusion_log(excluded_subjects, log_path)
    
    return valid_subjects
