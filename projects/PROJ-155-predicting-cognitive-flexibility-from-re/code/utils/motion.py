"""
Motion utilities for fMRI preprocessing.

Provides functions to calculate Mean Framewise Displacement (FD)
and apply exclusion logic based on configuration thresholds.
"""

import csv
import os
from typing import List, Dict, Tuple, Optional

import numpy as np
import nibabel as nib

from code.config import get_config


def calculate_mean_fd(nifti_path: str) -> float:
    """
    Calculate the Mean Framewise Displacement (FD) from a preprocessed 4D NIfTI file.

    This implementation assumes the file contains 6 motion parameters (3 translations, 3 rotations)
    as the last 6 volumes or embedded in the header, but standard HCP preprocessed data
    typically provides these in a separate .txt or .1D file. However, if the input is strictly
    the 4D image, we cannot derive FD without the motion parameters.

    To adhere to the "Real Data" constraint and the HCP pipeline context:
    This function expects the path to the motion parameter file (e.g., 'rfMRI_REST1_LR_hp2000_clean.dtseries.csv'
    or a specific .txt file containing 6 columns of motion parameters) if available, OR
    it attempts to derive it if the image has a specific extension containing the params.

    *Correction for HCP Context*: HCP provides motion parameters in a separate text file.
    To make this robust, we check for a companion motion file. If the input is the NIfTI,
    we look for a companion file with the same stem but 'motion' or 'params' in the name.
    If no motion file is found, we cannot calculate FD from the image data alone (image intensity
    does not equal motion parameters).

    For the purpose of this pipeline, we assume the input `nifti_path` is the imaging data,
    and we will look for a companion motion parameter file in the same directory.
    Standard HCP naming convention for motion parameters is often `<subject>_rfMRI_<task>_HP2000_clean.dtseries.csv`
    which contains time series, but the motion parameters are usually in a separate file like
    `<subject>_rfMRI_<task>_HP2000_clean_MotionParams.txt` or similar.

    Since the task requires calculating Mean FD, and FD is strictly derived from motion parameters:
    1. Attempt to load motion parameters from a companion file.
    2. If not found, raise an error indicating the missing dependency.

    Args:
        nifti_path: Path to the 4D NIfTI file.

    Returns:
        Mean FD value (float).

    Raises:
        FileNotFoundError: If motion parameters cannot be located.
        ValueError: If motion parameters are malformed.
    """
    base_path = os.path.splitext(nifti_path)[0]
    dir_name = os.path.dirname(nifti_path)
    stem = os.path.basename(base_path)

    # Common patterns for HCP motion parameter files
    # HCP often stores motion params in a .txt file or as part of the .dtseries.csv
    # We will search for a file with 'motion' or 'params' in the name in the same directory
    potential_files = []
    for filename in os.listdir(dir_name):
        if filename.startswith(stem) and ('motion' in filename.lower() or 'params' in filename.lower()):
            potential_files.append(os.path.join(dir_name, filename))

    if not potential_files:
        # Fallback: Try to find a generic motion file if the stem doesn't match perfectly
        # This is a heuristic. In a real HCP pipeline, the file names are specific.
        # If we can't find it, we must fail loudly as per constraints.
        raise FileNotFoundError(
            f"Motion parameter file not found for {nifti_path}. "
            f"Expected a companion file with 'motion' or 'params' in the name in {dir_name}. "
            f"HCP FD calculation requires motion parameters (6 DOF) which are not stored in the NIfTI image itself."
        )

    # Load the first found motion file
    # Assuming a text/csv format with 6 columns (3 trans, 3 rot)
    motion_params = None
    for f_path in potential_files:
        try:
            # Try loading as CSV (HCP often uses .txt or .csv)
            # Skip header if present, assume space or comma separated
            data = np.loadtxt(f_path, delimiter=None)
            if data.ndim == 1:
                data = data.reshape(-1, 6)
            if data.shape[1] == 6:
                motion_params = data
                break
        except Exception:
            continue

    if motion_params is None:
        raise ValueError(f"Could not parse motion parameters from {potential_files}")

    # Calculate FD
    # FD = sum(|dX|, |dY|, |dZ|, |dr|, |dp|, |dy|)
    # Rotations are in radians. Convert to mm: radius of head ~50mm
    # HCP standard: 50mm radius for rotation conversion
    radius = 50.0

    # Calculate absolute differences (delta)
    delta = np.abs(np.diff(motion_params, axis=0))

    # Apply rotation conversion
    # delta[:, 3:] corresponds to rotations (pitch, roll, yaw)
    delta_rot_mm = delta[:, 3:] * radius

    # Combine translation and rotation deltas
    # FD_t = |dX| + |dY| + |dZ| + |dPitch| + |dRoll| + |dYaw|
    fd_values = np.sum(np.hstack([delta[:, :3], delta_rot_mm]), axis=1)

    # Mean FD
    return float(np.mean(fd_values))


def check_motion_exclusion(mean_fd: float, threshold: Optional[float] = None) -> bool:
    """
    Check if a subject should be excluded based on Mean FD.

    Args:
        mean_fd: The calculated Mean Framewise Displacement.
        threshold: The exclusion threshold. If None, uses the value from config.

    Returns:
        True if the subject should be EXCLUDED (i.e., FD > threshold).
    """
    if threshold is None:
        config = get_config()
        threshold = config.get('FD_threshold', 0.2)

    return mean_fd > threshold


def generate_exclusion_log(
    subjects_data: List[Dict[str, any]],
    output_path: str
) -> Tuple[List[Dict], List[Dict]]:
    """
    Process a list of subject data, filter by motion, and write the exclusion log.

    Args:
        subjects_data: List of dicts containing 'Subject_ID', 'Mean_FD', and other metadata.
        output_path: Path to the CSV file to write the exclusion log.

    Returns:
        Tuple of (included_subjects, excluded_subjects).
    """
    config = get_config()
    threshold = config.get('FD_threshold', 0.2)

    included = []
    excluded = []

    for subject in subjects_data:
        sub_id = subject.get('Subject_ID')
        mean_fd = subject.get('Mean_FD')

        if mean_fd is None:
            # Cannot evaluate, treat as excluded or error?
            # For now, log as excluded with reason "Missing_FD"
            excluded.append({
                'Subject_ID': sub_id,
                'Exclusion_Reason': 'Missing_FD',
                'Mean_FD': None
            })
            continue

        if check_motion_exclusion(mean_fd, threshold):
            excluded.append({
                'Subject_ID': sub_id,
                'Exclusion_Reason': 'Motion',
                'Mean_FD': mean_fd
            })
        else:
            included.append(subject)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write exclusion log
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Subject_ID', 'Exclusion_Reason', 'Mean_FD'])
        writer.writeheader()
        for row in excluded:
            # Format Mean_FD for CSV
            fd_val = row['Mean_FD']
            row['Mean_FD'] = f"{fd_val:.4f}" if fd_val is not None else ""
            writer.writerow(row)

    return included, excluded
