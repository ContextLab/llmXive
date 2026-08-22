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
        motion_params: numpy array of shape (n_timepoints, 6) containing 
                       translation (x, y, z) and rotation (roll, pitch, yaw).
    
    Returns:
        Mean FD value in mm.
    """
    if motion_params.shape[1] != 6:
        raise ValueError(f"Motion params must have 6 columns, got {motion_params.shape[1]}")
    
    # Convert rotation from radians to mm (assuming 50mm radius of rotation)
    # FD = sum(|dx|) + sum(|dy|) + sum(|dz|) + sum(50 * |droll|) + sum(50 * |dpitch|) + sum(50 * |dyaw|)
    # We calculate deltas (differences between consecutive timepoints)
    
    deltas = np.diff(motion_params, axis=0)
    
    # Absolute displacements for translation (already in mm)
    trans_deltas = np.abs(deltas[:, :3])
    
    # Absolute displacements for rotation (convert radians to mm)
    rot_deltas = 50.0 * np.abs(deltas[:, 3:])
    
    # FD per timepoint
    fd_per_tp = np.sum(trans_deltas, axis=1) + np.sum(rot_deltas, axis=1)
    
    # Mean FD (excluding the first timepoint which has no delta)
    mean_fd = np.mean(fd_per_tp)
    
    return float(mean_fd)


def load_motion_params_from_nifti(nifti_path: str) -> np.ndarray:
    """
    Load motion parameters from a .par/.rec file or extract from NIfTI header if available.
    For HCP data, motion parameters are typically stored in separate files.
    This function attempts to load them from the standard HCP location.
    
    Args:
        nifti_path: Path to the NIfTI file (used to infer subject ID and location).
    
    Returns:
        numpy array of motion parameters (n_timepoints, 6).
    """
    # HCP data structure: Subject ID is derived from the filename
    # Motion parameters are usually in <subject_id>/MNINonLinear/Results/<session>/<session>_rfMRI.dtseries.nii
    # But motion parameters are in <subject_id>/MNINonLinear/Results/<session>/<session>_rfMRI_MotionParams.par
    
    subject_id = os.path.basename(os.path.dirname(nifti_path))
    parent_dir = os.path.dirname(os.path.dirname(nifti_path))
    
    # HCP typically stores motion parameters in a .par file
    # Look for the standard HCP motion parameter file
    motion_file = os.path.join(
        parent_dir, 
        subject_id, 
        "MNINonLinear", 
        "Results", 
        "rfMRI_REST1_LR", 
        f"{subject_id}_rfMRI_REST1_LR_MotionParams.par"
    )
    
    if not os.path.exists(motion_file):
        # Try alternative path (rfMRI_REST2_RL)
        motion_file = os.path.join(
            parent_dir, 
            subject_id, 
            "MNINonLinear", 
            "Results", 
            "rfMRI_REST2_RL", 
            f"{subject_id}_rfMRI_REST2_RL_MotionParams.par"
        )
    
    if not os.path.exists(motion_file):
        raise FileNotFoundError(f"Motion parameters file not found for {subject_id}. "
                              f"Expected at: {motion_file}")
    
    # Parse the .par file (HCP format: 6 columns, whitespace delimited)
    motion_params = []
    with open(motion_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    values = [float(x) for x in line.split()]
                    if len(values) == 6:
                        motion_params.append(values)
                except ValueError:
                    continue
    
    if not motion_params:
        raise ValueError(f"No valid motion parameters found in {motion_file}")
    
    return np.array(motion_params)


def check_motion_exclusion(mean_fd: float, threshold: Optional[float] = None) -> Tuple[bool, str]:
    """
    Check if a subject should be excluded based on Mean FD.
    
    Args:
        mean_fd: Calculated Mean Framewise Displacement.
        threshold: FD threshold for exclusion. Defaults to config value (0.2mm).
    
    Returns:
        Tuple of (should_exclude, reason_string)
    """
    if threshold is None:
        config = get_config()
        threshold = config.get('FD_threshold', 0.2)
    
    if mean_fd > threshold:
        return True, f"Motion (Mean_FD={mean_fd:.4f} > {threshold})"
    
    return False, ""


def generate_exclusion_log(excluded_subjects: List[Dict[str, Any]], log_path: Optional[str] = None) -> str:
    """
    Write excluded subjects to the exclusion log CSV.
    
    Args:
        excluded_subjects: List of dicts with keys: Subject_ID, Exclusion_Reason, Mean_FD.
        log_path: Path to the exclusion log. Defaults to processed/exclusion_log.csv.
    
    Returns:
        Path to the written log file.
    """
    if log_path is None:
        log_path = get_exclusion_log_path()
    
    ensure_dir(os.path.dirname(log_path))
    
    fieldnames = ['Subject_ID', 'Exclusion_Reason', 'Mean_FD']
    
    file_exists = os.path.exists(log_path)
    
    with open(log_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for subject in excluded_subjects:
            writer.writerow({
                'Subject_ID': subject['Subject_ID'],
                'Exclusion_Reason': subject['Exclusion_Reason'],
                'Mean_FD': f"{subject['Mean_FD']:.6f}"
            })
    
    logger.info(f"Updated exclusion log at {log_path} with {len(excluded_subjects)} entries")
    return log_path


def process_subject_motion(subject_id: str, nifti_path: str, threshold: Optional[float] = None) -> Dict[str, Any]:
    """
    Process a single subject's motion parameters and determine exclusion status.
    
    Args:
        subject_id: Subject identifier.
        nifti_path: Path to the preprocessed NIfTI file.
        threshold: FD threshold for exclusion.
    
    Returns:
        Dict with keys: Subject_ID, Mean_FD, Excluded, Exclusion_Reason
    """
    try:
        motion_params = load_motion_params_from_nifti(nifti_path)
        mean_fd = calculate_mean_fd(motion_params)
        
        should_exclude, reason = check_motion_exclusion(mean_fd, threshold)
        
        return {
            'Subject_ID': subject_id,
            'Mean_FD': mean_fd,
            'Excluded': should_exclude,
            'Exclusion_Reason': reason
        }
    
    except FileNotFoundError as e:
        logger.error(f"Motion parameters not found for {subject_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing motion for {subject_id}: {e}")
        raise


def run_motion_filtering_pipeline(subject_ids: List[str], nifti_paths: List[str], threshold: Optional[float] = None) -> Tuple[List[Dict], List[Dict]]:
    """
    Run the motion filtering pipeline on a list of subjects.
    
    Args:
        subject_ids: List of subject identifiers.
        nifti_paths: List of paths to preprocessed NIfTI files.
        threshold: FD threshold for exclusion.
    
    Returns:
        Tuple of (included_subjects, excluded_subjects)
        Each is a list of dicts with Subject_ID, Mean_FD, Exclusion_Reason (if excluded).
    """
    if len(subject_ids) != len(nifti_paths):
        raise ValueError("subject_ids and nifti_paths must have the same length")
    
    included = []
    excluded = []
    
    for subject_id, nifti_path in zip(subject_ids, nifti_paths):
        try:
            result = process_subject_motion(subject_id, nifti_path, threshold)
            
            if result['Excluded']:
                excluded.append({
                    'Subject_ID': result['Subject_ID'],
                    'Exclusion_Reason': 'Motion',
                    'Mean_FD': result['Mean_FD']
                })
                log_exclusion(
                    subject_id=result['Subject_ID'],
                    reason='Motion',
                    details=f"Mean_FD={result['Mean_FD']:.4f}"
                )
            else:
                included.append({
                    'Subject_ID': result['Subject_ID'],
                    'Mean_FD': result['Mean_FD']
                })
        
        except Exception as e:
            logger.error(f"Skipping {subject_id} due to error: {e}")
            # Treat errors as exclusions? Or skip? 
            # For now, skip and log error, do not add to either list
            continue
    
    # Write exclusion log
    if excluded:
        generate_exclusion_log(excluded)
    
    logger.info(f"Motion filtering complete: {len(included)} included, {len(excluded)} excluded")
    return included, excluded


def main():
    """
    Main entry point for motion filtering.
    Reads subject list from processed data, applies motion filtering, 
    and writes exclusion log.
    """
    config = get_config()
    threshold = config.get('FD_threshold', 0.2)
    
    # Get list of subjects from processed directory
    processed_path = get_processed_path()
    
    # Assume subjects are organized as processed/<subject_id>/...
    # For now, we'll use a placeholder list. In real execution, 
    # this would be populated from the actual processed data.
    # This function is typically called by a higher-level pipeline.
    
    logger.warning("Motion filtering main() requires explicit subject list. "
                  "Call run_motion_filtering_pipeline() with subject_ids and nifti_paths.")


if __name__ == "__main__":
    main()
