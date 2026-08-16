import csv
import os
import logging
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
import nibabel as nib
from code.config import get_config
from code.utils.logging import log_exclusion, get_exclusion_log_path, init_logging
from code.data.paths import get_processed_path, get_raw_path, ensure_dir

def calculate_mean_fd(motion_params: np.ndarray) -> float:
    """
    Calculate the Mean Framewise Displacement (FD) from 6 motion parameters.
    
    Args:
        motion_params: Array of shape (n_timepoints, 6) containing 
                       [trans_x, trans_y, trans_z, rot_x, rot_y, rot_z]
    
    Returns:
        float: Mean FD value in mm.
    """
    if motion_params.shape[1] != 6:
        raise ValueError(f"Expected 6 motion parameters, got {motion_params.shape[1]}")
    
    # Jacobian approximation for rotation to mm (assuming 50mm radius)
    # FD = |Δdx| + |Δdy| + |Δdz| + 50*(|Δdrx| + |Δdry| + |Δdrz|)
    # Note: Rotations are typically in radians in NIfTI headers
    n_tp = motion_params.shape[0]
    if n_tp < 2:
        return 0.0
    
    # Calculate absolute differences between consecutive timepoints
    diffs = np.abs(np.diff(motion_params, axis=0))
    
    # Sum translation diffs and rotation diffs (scaled by 50mm)
    # diffs[:, 0:3] are translations (mm), diffs[:, 3:6] are rotations (rad)
    fd_values = np.sum(diffs[:, 0:3], axis=1) + 50.0 * np.sum(diffs[:, 3:6], axis=1)
    
    return float(np.mean(fd_values))

def load_motion_params_from_nifti(nifti_path: str) -> np.ndarray:
    """
    Load motion parameters from a preprocessed NIfTI file's sidecar or 
    extract from the file if stored in a specific manner.
    
    For HCP data, motion parameters are often stored in separate .tsv files
    or embedded in the preprocessing logs. This function attempts to find
    the standard HCP motion parameter file associated with the subject.
    
    Args:
        nifti_path: Path to the preprocessed NIfTI file.
    
    Returns:
        np.ndarray: Motion parameters array (n_timepoints, 6).
    
    Raises:
        FileNotFoundError: If motion parameters cannot be located.
    """
    # HCP typically stores motion parameters in a .tsv file next to the NIfTI
    # or in the 'MNINonLinear/Results' directory structure.
    # We look for a file named <subject>_rfn_MSMAll_hp2000_clean.dtf.nii.gz
    # and its corresponding motion parameter file.
    
    base_dir = os.path.dirname(nifti_path)
    subject_id = os.path.basename(base_dir)
    
    # Common HCP motion parameter file patterns
    possible_names = [
        f"{subject_id}_rfn_MSMAll_hp2000_clean.dtf.nii.gz", # This is the image, we need params
        f"{subject_id}_rfn_MSMAll_hp2000_clean.par",
        f"{subject_id}_rfn_MSMAll_hp2000_clean.tsv",
        os.path.join(base_dir, "Movement_Regressors.txt")
    ]
    
    # If we can't find a specific sidecar, we might need to rely on the 
    # fact that the task T012/T013/T014 pipeline has already extracted 
    # the time series and potentially the motion parameters into a CSV.
    # However, for strict adherence to "real data", we assume the raw 
    # download includes the necessary files.
    
    # Fallback: Try to load from the standard HCP directory structure
    # HCP 1200 release structure: <Subject>/MNINonLinear/Results/rfMRI_REST1_LR/
    # The motion parameters are often in the 'Movement_Regressors.txt'
    
    # Since we are in the processed stage, let's assume the motion params 
    # were saved alongside the time series or can be recalculated if 
    # the raw data is still accessible.
    
    # For this implementation, we assume the existence of a file 
    # 'motion_params.csv' generated during T013 preprocessing or T012 download
    # if not found, we raise an error to fail loudly as per constraints.
    
    # Let's look for a standard HCP motion file relative to the NIfTI
    # In HCP, the file is often: <Subject>/MNINonLinear/Results/rfMRI_REST1_LR/<Subject>_rfn_MSMAll_hp2000_clean.dtf.nii.gz
    # And the motion file is: <Subject>/MNINonLinear/Results/rfMRI_REST1_LR/<Subject>_rfn_MSMAll_hp2000_clean.par
    
    # We will construct the path to the .par file if it exists
    # If not, we look for a .txt file
    
    # Attempt 1: Look for .par file (FSL format)
    base_name = os.path.splitext(os.path.basename(nifti_path))[0]
    parent_dir = os.path.dirname(nifti_path)
    
    # Try to find motion params in the same directory or a standard location
    # If T013 created a CSV of time series, it might have also saved motion params.
    # Let's assume a standard location for this project: data/processed/motion_params.csv
    
    # Actually, the most robust way for HCP is to read the .par file if available
    # or the .txt file.
    
    # Let's assume the path provided is the preprocessed NIfTI.
    # We will look for the motion parameters in the same directory.
    # If not found, we check the raw data directory.
    
    # For the purpose of this task, we assume the motion parameters are stored
    # in a CSV file named 'motion_params.csv' in the same directory as the NIfTI
    # or in a dedicated 'motion' subdirectory.
    
    # If we cannot find the motion parameters, we must fail loudly.
    
    # Let's try to read from a standard HCP location if the NIfTI path is deep
    # e.g., .../MNINonLinear/Results/rfMRI_REST1_LR/subject.nii.gz
    # The motion file is .../MNINonLinear/Results/rfMRI_REST1_LR/subject.par
    
    potential_par = os.path.join(parent_dir, base_name + ".par")
    if os.path.exists(potential_par):
        # FSL .par files are space-separated
        data = np.loadtxt(potential_par)
        return data
    
    potential_txt = os.path.join(parent_dir, "Movement_Regressors.txt")
    if os.path.exists(potential_txt):
        # HCP Movement_Regressors.txt is space/tab separated, 6 columns
        data = np.loadtxt(potential_txt)
        return data

    # If we are in the processed folder, maybe T013 saved it?
    # Let's check for a generic motion_params.csv in the processed dir
    processed_path = get_processed_path()
    if os.path.exists(os.path.join(processed_path, "motion_params.csv")):
        # This would require mapping subject IDs, which is complex without context
        # We will assume the file is in the same directory as the NIfTI for now
        # or fail.
        pass

    raise FileNotFoundError(f"Motion parameters not found for {nifti_path}. "
                            f"Checked {potential_par} and {potential_txt}. "
                            "Ensure T012/T013 have downloaded and processed the raw data correctly.")

def check_motion_exclusion(mean_fd: float, threshold: Optional[float] = None) -> Tuple[bool, str]:
    """
    Check if a subject should be excluded based on Mean FD.
    
    Args:
        mean_fd: The calculated Mean FD.
        threshold: The FD threshold. Defaults to config value (0.2).
    
    Returns:
        Tuple[bool, str]: (should_exclude, reason)
    """
    if threshold is None:
        config = get_config()
        threshold = config.get("FD_threshold", 0.2)
    
    if mean_fd > threshold:
        return True, "Motion"
    return False, ""

def generate_exclusion_log(subject_id: str, reason: str, mean_fd: float, log_path: str):
    """
    Append a single exclusion record to the CSV log.
    
    Args:
        subject_id: The subject identifier.
        reason: The reason for exclusion (e.g., "Motion").
        mean_fd: The calculated Mean FD.
        log_path: Path to the exclusion log CSV.
    """
    ensure_dir(log_path)
    file_exists = os.path.exists(log_path)
    
    with open(log_path, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Subject_ID', 'Exclusion_Reason', 'Mean_FD'])
        writer.writerow([subject_id, reason, f"{mean_fd:.6f}"])

def process_subject_motion(nifti_path: str, subject_id: str, log_path: str) -> Optional[Dict[str, Any]]:
    """
    Process motion for a single subject: load params, calculate FD, check exclusion.
    
    Args:
        nifti_path: Path to the subject's NIfTI file.
        subject_id: Subject ID string.
        log_path: Path to the exclusion log.
    
    Returns:
        Dict with 'subject_id', 'mean_fd', 'excluded' if successful.
        None if the file is missing or an error occurs (will be logged).
    """
    try:
        motion_params = load_motion_params_from_nifti(nifti_path)
        mean_fd = calculate_mean_fd(motion_params)
        should_exclude, reason = check_motion_exclusion(mean_fd)
        
        if should_exclude:
            generate_exclusion_log(subject_id, reason, mean_fd, log_path)
            log_exclusion(subject_id, reason, f"Mean_FD={mean_fd:.4f}")
        
        return {
            "subject_id": subject_id,
            "mean_fd": mean_fd,
            "excluded": should_exclude
        }
    except FileNotFoundError as e:
        logging.error(f"Missing motion data for {subject_id}: {e}")
        return None
    except Exception as e:
        logging.error(f"Error processing motion for {subject_id}: {e}")
        return None

def run_motion_filtering_pipeline(subjects: List[Dict[str, Any]], log_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Run the motion filtering pipeline on a list of subjects.
    
    Args:
        subjects: List of dicts containing 'subject_id' and 'nifti_path'.
        log_path: Optional path for the exclusion log. If None, uses default from config.
    
    Returns:
        List of valid subjects (those not excluded by motion).
    """
    if log_path is None:
        log_path = get_exclusion_log_path()
    
    ensure_dir(log_path)
    valid_subjects = []
    
    # Initialize log header if file doesn't exist
    if not os.path.exists(log_path):
        with open(log_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Subject_ID', 'Exclusion_Reason', 'Mean_FD'])
    
    for sub in subjects:
        sub_id = sub['subject_id']
        nifti_path = sub['nifti_path']
        
        result = process_subject_motion(nifti_path, sub_id, log_path)
        
        if result and not result['excluded']:
            valid_subjects.append(sub)
        elif result and result['excluded']:
            # Already logged in process_subject_motion
            pass
        else:
            # Error occurred, exclude the subject
            log_exclusion(sub_id, "Error", "Motion processing failed")
            generate_exclusion_log(sub_id, "Error", 0.0, log_path)
    
    return valid_subjects
