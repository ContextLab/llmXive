import csv
import os
import logging
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
import nibabel as nib

from code.config import get_config
from code.data.paths import get_processed_path, get_raw_path, ensure_dir
from code.utils.logging import log_exclusion, get_exclusion_log_path

logger = logging.getLogger(__name__)

def calculate_mean_fd(motion_params: np.ndarray) -> float:
    """
    Calculate the Mean Framewise Displacement (FD) from 6 motion parameters.
    
    Args:
        motion_params: Array of shape (n_timepoints, 6) containing
                       [trans_x, trans_y, trans_z, rot_x, rot_y, rot_z]
    
    Returns:
        Mean FD value in mm.
    """
    if motion_params.shape[1] != 6:
        raise ValueError(f"Expected 6 motion parameters, got {motion_params.shape[1]}")
    
    # Translational differences (mm)
    trans_diff = np.abs(np.diff(motion_params[:, 0:3], axis=0), axis=1)
    
    # Rotational differences (radians) -> convert to mm (assuming 50mm radius)
    # Power et al. (2012) convention: 50mm radius for rotation to mm conversion
    rot_diff = np.abs(np.diff(motion_params[:, 3:6], axis=0), axis=1) * 50.0
    
    # FD per frame: sum of absolute differences
    fd_per_frame = np.sum(trans_diff, axis=1) + np.sum(rot_diff, axis=1)
    
    # Mean FD across all frames (excluding the first frame which has no diff)
    mean_fd = np.mean(fd_per_frame)
    
    return float(mean_fd)

def load_motion_params_from_nifti(nifti_path: str) -> np.ndarray:
    """
    Load motion parameters from a preprocessed fMRI NIfTI file.
    
    Note: In HCP data, motion parameters are often stored in a separate
    .txt or .1D file alongside the NIfTI. If not found in the NIfTI
    header or sidecar, this function attempts to load from a standard
    sidecar file or raises an error if not found.
    
    For this implementation, we assume motion parameters are stored in
    a sidecar text file named <subject>_movement_params.txt or similar.
    If the NIfTI itself contains the motion parameters (e.g., in a specific
    extension), we extract them there.
    
    Args:
        nifti_path: Path to the preprocessed NIfTI file.
    
    Returns:
        numpy array of motion parameters (n_timepoints, 6).
    
    Raises:
        FileNotFoundError: If motion parameters cannot be found.
    """
    base_path = os.path.splitext(nifti_path)[0]
    
    # Common sidecar patterns for HCP data
    possible_sidecars = [
        f"{base_path}_movement_params.txt",
        f"{base_path}_movement_params.1D",
        f"{os.path.basename(base_path)}_movement_params.txt",
    ]
    
    motion_file = None
    for candidate in possible_sidecars:
        if os.path.exists(candidate):
            motion_file = candidate
            break
    
    if motion_file is None:
        # Try to find any .txt or .1D file in the same directory with 'movement' or 'motion'
        dir_path = os.path.dirname(nifti_path)
        for f in os.listdir(dir_path):
            if ('movement' in f.lower() or 'motion' in f.lower()) and (f.endswith('.txt') or f.endswith('.1D')):
                motion_file = os.path.join(dir_path, f)
                break
    
    if motion_file is None:
        raise FileNotFoundError(
            f"Could not find motion parameters for {nifti_path}. "
            "Expected a sidecar file with 'movement' or 'motion' in the name."
        )
    
    # Load motion parameters
    try:
        params = np.loadtxt(motion_file)
        if params.ndim == 1:
            params = params.reshape(-1, 6)
        if params.shape[1] != 6:
            logger.warning(f"Motion file {motion_file} has {params.shape[1]} columns, expected 6. Using first 6.")
            params = params[:, :6]
        return params
    except Exception as e:
        raise RuntimeError(f"Failed to load motion parameters from {motion_file}: {e}")

def check_motion_exclusion(mean_fd: float, threshold: Optional[float] = None) -> bool:
    """
    Check if a subject should be excluded based on Mean FD threshold.
    
    Args:
        mean_fd: Calculated Mean FD value.
        threshold: FD threshold for exclusion. Defaults to config value (0.2mm).
    
    Returns:
        True if the subject should be excluded (Mean FD > threshold).
    """
    if threshold is None:
        config = get_config()
        threshold = config.get('FD_threshold', 0.2)
    
    return mean_fd > threshold

def generate_exclusion_log(
    subject_id: str, 
    mean_fd: float, 
    reason: str = "Motion",
    log_path: Optional[str] = None
) -> str:
    """
    Log an exclusion entry to the exclusion log CSV.
    
    Args:
        subject_id: The subject identifier.
        mean_fd: The calculated Mean FD value.
        reason: The reason for exclusion (default: "Motion").
        log_path: Optional path to the exclusion log. Defaults to processed/exclusion_log.csv.
    
    Returns:
        Path to the updated exclusion log.
    """
    if log_path is None:
        log_path = get_exclusion_log_path()
    
    ensure_dir(os.path.dirname(log_path))
    
    file_exists = os.path.exists(log_path)
    
    with open(log_path, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Subject_ID', 'Exclusion_Reason', 'Mean_FD'])
        writer.writerow([subject_id, reason, f"{mean_fd:.6f}"])
    
    logger.info(f"Logged exclusion for {subject_id}: {reason} (Mean_FD={mean_fd:.4f})")
    return log_path

def process_subject_motion(
    subject_id: str, 
    nifti_path: str, 
    threshold: Optional[float] = None
) -> Tuple[bool, float]:
    """
    Process a single subject's motion data: calculate Mean FD and check exclusion.
    
    Args:
        subject_id: The subject identifier.
        nifti_path: Path to the preprocessed NIfTI file.
        threshold: FD threshold for exclusion. Defaults to config value.
    
    Returns:
        Tuple of (should_exclude: bool, mean_fd: float).
    
    Raises:
        FileNotFoundError: If motion parameters are missing.
        RuntimeError: If motion calculation fails.
    """
    try:
        motion_params = load_motion_params_from_nifti(nifti_path)
        mean_fd = calculate_mean_fd(motion_params)
        should_exclude = check_motion_exclusion(mean_fd, threshold)
        
        if should_exclude:
            generate_exclusion_log(subject_id, mean_fd, "Motion")
            logger.warning(f"Subject {subject_id} excluded due to motion (Mean_FD={mean_fd:.4f} > {threshold})")
        
        return should_exclude, mean_fd
        
    except FileNotFoundError as e:
        logger.error(f"Motion parameters not found for {subject_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing motion for {subject_id}: {e}")
        raise

def run_motion_filtering_pipeline(
    subject_ids: List[str], 
    nifti_paths: Dict[str, str], 
    threshold: Optional[float] = None,
    output_csv: Optional[str] = None
) -> Tuple[List[str], Dict[str, float]]:
    """
    Run the motion filtering pipeline on a list of subjects.
    
    Args:
        subject_ids: List of subject IDs to process.
        nifti_paths: Dictionary mapping subject_id to their NIfTI path.
        threshold: FD threshold for exclusion. Defaults to config value.
        output_csv: Optional path to save the full exclusion log (defaults to get_exclusion_log_path()).
    
    Returns:
        Tuple of (valid_subject_ids: List[str], all_mean_fds: Dict[str, float]).
        valid_subject_ids are those NOT excluded by motion.
        all_mean_fds contains Mean FD for all processed subjects.
    """
    if output_csv is None:
        output_csv = get_exclusion_log_path()
    
    # Clear the log file at the start of the pipeline run if it exists
    # to ensure we only log exclusions from this run (or append if intended as cumulative)
    # Per task requirement: "Log excluded subjects". We append to the file.
    # However, to avoid duplicates on re-runs, we might want to clear it first.
    # Given the task says "Log excluded subjects", we will append.
    # But for a clean run, let's ensure the file exists with headers if it's a new run.
    # The function generate_exclusion_log handles header creation.
    
    valid_subjects = []
    all_mean_fds = {}
    
    logger.info(f"Starting motion filtering pipeline for {len(subject_ids)} subjects.")
    
    for subject_id in subject_ids:
        if subject_id not in nifti_paths:
            logger.error(f"Subject {subject_id} not found in nifti_paths mapping. Skipping.")
            continue
        
        nifti_path = nifti_paths[subject_id]
        
        if not os.path.exists(nifti_path):
            logger.error(f"NIfTI file not found for {subject_id}: {nifti_path}. Skipping.")
            continue
        
        try:
            should_exclude, mean_fd = process_subject_motion(subject_id, nifti_path, threshold)
            all_mean_fds[subject_id] = mean_fd
            
            if not should_exclude:
                valid_subjects.append(subject_id)
            else:
                # Already logged in process_subject_motion
                pass
                
        except Exception as e:
            logger.error(f"Failed to process motion for {subject_id}: {e}")
            # Do not include in valid subjects
            continue
    
    logger.info(f"Motion filtering complete. {len(valid_subjects)} subjects passed, {len(subject_ids) - len(valid_subjects)} excluded.")
    return valid_subjects, all_mean_fds

# Helper to ensure the exclusion log path is correct
def get_exclusion_log_path() -> str:
    """
    Get the path to the exclusion log CSV.
    
    Returns:
        Absolute path to data/processed/exclusion_log.csv.
    """
    processed_path = get_processed_path()
    return os.path.join(processed_path, "exclusion_log.csv")

# Re-export for clarity in imports
__all__ = [
    'calculate_mean_fd',
    'load_motion_params_from_nifti',
    'check_motion_exclusion',
    'generate_exclusion_log',
    'process_subject_motion',
    'run_motion_filtering_pipeline',
    'get_exclusion_log_path'
]
