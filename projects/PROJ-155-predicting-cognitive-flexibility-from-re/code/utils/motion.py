"""
Motion filtering utilities for fMRI data processing.

This module handles Mean FD calculation, motion exclusion logic,
and generation of exclusion logs for subjects exceeding motion thresholds.
"""
import csv
import os
import logging
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
import nibabel as nib
import pandas as pd

from code.config import get_config
from code.data.paths import get_processed_path, get_raw_path, ensure_dir
from code.utils.logging import log_exclusion, get_exclusion_log_path, init_logging

logger = logging.getLogger(__name__)

def calculate_mean_fd(motion_params: np.ndarray) -> float:
    """
    Calculate the Mean Framewise Displacement (FD) from motion parameters.
    
    Args:
        motion_params: Array of shape (n_timepoints, 6) containing
                     3 translation (mm) and 3 rotation (rad) parameters.
                     
    Returns:
        Mean FD value in mm.
    """
    if motion_params.shape[1] != 6:
        raise ValueError(f"Expected 6 motion parameters, got {motion_params.shape[1]}")
    
    # Extract translations and rotations
    translations = motion_params[:, :3]  # x, y, z in mm
    rotations = motion_params[:, 3:]     # roll, pitch, yaw in radians
    
    # Calculate absolute differences (differences between consecutive volumes)
    # FD is defined as the sum of absolute differences
    d_trans = np.abs(np.diff(translations, axis=0))
    d_rot = np.abs(np.diff(rotations, axis=0))
    
    # Convert rotation differences to displacement (assuming 50mm radius)
    # This is the standard Power et al. (2012) definition
    radius = 50.0
    d_rot_disp = radius * d_rot
    
    # Calculate FD for each volume (excluding the first one which has no previous)
    fd_per_volume = np.sum(d_trans, axis=1) + np.sum(d_rot_disp, axis=1)
    
    # Mean FD across all volumes
    mean_fd = np.mean(fd_per_volume)
    
    return float(mean_fd)

def load_motion_params_from_nifti(nifti_path: str) -> np.ndarray:
    """
    Load motion parameters from a NIfTI file containing 6 motion regressors.
    
    Args:
        nifti_path: Path to the NIfTI file containing motion parameters.
                    
    Returns:
        Array of shape (n_timepoints, 6) with motion parameters.
    """
    if not os.path.exists(nifti_path):
        raise FileNotFoundError(f"Motion parameters file not found: {nifti_path}")
    
    # Try to load as NIfTI (some motion files are stored as 4D NIfTI)
    try:
        img = nib.load(nifti_path)
        data = img.get_fdata()
        
        # If 4D, reshape to (n_timepoints, 6) assuming 6 volumes per timepoint
        # or if it's actually a 2D matrix stored in 4D format
        if len(data.shape) == 4:
            # Check if it's 6 volumes (one per parameter)
            if data.shape[3] == 6:
                # Reshape to (n_timepoints, 6)
                data = np.moveaxis(data, -1, 0)
                data = data.reshape(-1, 6)
            else:
                # Try to interpret as (n_timepoints, 6) directly
                # Flatten and reshape
                flat = data.flatten()
                if len(flat) % 6 == 0:
                    data = flat.reshape(-1, 6)
                else:
                    raise ValueError(f"Cannot reshape motion data: {data.shape}")
        
        return data.astype(np.float64)
    except Exception as e:
        logger.warning(f"Failed to load as NIfTI, trying CSV: {e}")
        # Try loading as CSV (some pipelines save motion params as CSV)
        if nifti_path.lower().endswith('.csv'):
            df = pd.read_csv(nifti_path, header=None)
            return df.values.astype(np.float64)
        else:
            # Try to read as text file with 6 columns
            try:
                data = np.loadtxt(nifti_path)
                if data.ndim == 1:
                    data = data.reshape(-1, 6)
                return data.astype(np.float64)
            except:
                raise ValueError(f"Could not parse motion parameters from {nifti_path}")

def check_motion_exclusion(mean_fd: float, threshold: Optional[float] = None) -> bool:
    """
    Check if a subject should be excluded based on Mean FD threshold.
    
    Args:
        mean_fd: The Mean Framewise Displacement value in mm.
        threshold: FD threshold for exclusion. If None, uses config value.
                    
    Returns:
        True if subject should be excluded (Mean FD > threshold).
    """
    if threshold is None:
        config = get_config()
        threshold = config.get('FD_threshold', 0.2)
    
    return mean_fd > threshold

def generate_exclusion_log(excluded_subjects: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """
    Generate a CSV log of excluded subjects.
    
    Args:
        excluded_subjects: List of dicts with keys:
                           - Subject_ID
                           - Exclusion_Reason
                           - Mean_FD
        output_path: Path to write the exclusion log. If None, uses default path.
                    
    Returns:
        Path to the generated exclusion log.
    """
    if output_path is None:
        output_path = get_exclusion_log_path()
    
    ensure_dir(os.path.dirname(output_path))
    
    # Write header and data
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Subject_ID', 'Exclusion_Reason', 'Mean_FD'])
        writer.writeheader()
        writer.writerows(excluded_subjects)
    
    logger.info(f"Exclusion log written to {output_path} with {len(excluded_subjects)} entries")
    return output_path

def process_subject_motion(subject_id: str, motion_file_path: str, threshold: Optional[float] = None) -> Tuple[str, float, bool]:
    """
    Process motion parameters for a single subject and determine exclusion.
    
    Args:
        subject_id: The subject identifier.
        motion_file_path: Path to the motion parameters file.
        threshold: FD threshold for exclusion.
                    
    Returns:
        Tuple of (Subject_ID, Mean_FD, should_exclude)
    """
    try:
        motion_params = load_motion_params_from_nifti(motion_file_path)
        mean_fd = calculate_mean_fd(motion_params)
        should_exclude = check_motion_exclusion(mean_fd, threshold)
        
        if should_exclude:
            log_exclusion(
                subject_id=subject_id,
                reason="Motion",
                details=f"Mean_FD={mean_fd:.4f} > threshold={threshold}"
            )
            logger.info(f"Subject {subject_id} excluded due to motion: Mean_FD={mean_fd:.4f}")
        else:
            logger.debug(f"Subject {subject_id} passed motion filter: Mean_FD={mean_fd:.4f}")
        
        return subject_id, mean_fd, should_exclude
        
    except Exception as e:
        logger.error(f"Error processing motion for {subject_id}: {e}")
        raise

def run_motion_filtering_pipeline(input_csv_path: Optional[str] = None, 
                                 output_csv_path: Optional[str] = None,
                                 threshold: Optional[float] = None) -> Tuple[str, int, int]:
    """
    Run the full motion filtering pipeline on merged data.
    
    Reads merged data (from T014), calculates Mean_FD for each subject,
    excludes those exceeding the threshold, and writes an exclusion log.
    
    Args:
        input_csv_path: Path to the merged data CSV. If None, uses default processed path.
        output_csv_path: Path to write the filtered data. If None, uses default.
        threshold: FD threshold for exclusion. If None, uses config value.
                    
    Returns:
        Tuple of (output_path, total_subjects, excluded_count)
    """
    # Initialize logging
    init_logging()
    
    if threshold is None:
        config = get_config()
        threshold = config.get('FD_threshold', 0.2)
    
    # Determine input path
    if input_csv_path is None:
        input_csv_path = os.path.join(get_processed_path(), 'merged_data.csv')
    
    if not os.path.exists(input_csv_path):
        raise FileNotFoundError(f"Input merged data not found at {input_csv_path}")
    
    logger.info(f"Loading merged data from {input_csv_path}")
    df = pd.read_csv(input_csv_path)
    
    # Ensure required columns exist
    required_cols = ['Subject_ID', 'Mean_FD']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input data: {missing_cols}")
    
    total_subjects = len(df)
    logger.info(f"Loaded {total_subjects} subjects")
    
    # Filter subjects
    excluded_subjects = []
    filtered_df = df[df['Mean_FD'] <= threshold].copy()
    excluded_df = df[df['Mean_FD'] > threshold].copy()
    
    # Prepare exclusion log data
    for _, row in excluded_df.iterrows():
        excluded_subjects.append({
            'Subject_ID': str(row['Subject_ID']),
            'Exclusion_Reason': 'Motion',
            'Mean_FD': float(row['Mean_FD'])
        })
    
    excluded_count = len(excluded_subjects)
    kept_count = len(filtered_df)
    
    logger.info(f"Motion filtering complete: {excluded_count} excluded, {kept_count} kept (threshold={threshold})")
    
    # Write exclusion log
    exclusion_log_path = get_exclusion_log_path()
    if excluded_subjects:
        generate_exclusion_log(excluded_subjects, exclusion_log_path)
    else:
        # Create empty log with header
        with open(exclusion_log_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Subject_ID', 'Exclusion_Reason', 'Mean_FD'])
            writer.writeheader()
        logger.info("No subjects excluded for motion; created empty exclusion log")
    
    # Write filtered data
    if output_csv_path is None:
        output_csv_path = os.path.join(get_processed_path(), 'filtered_data.csv')
    
    ensure_dir(os.path.dirname(output_csv_path))
    filtered_df.to_csv(output_csv_path, index=False)
    logger.info(f"Filtered data written to {output_csv_path}")
    
    return output_csv_path, total_subjects, excluded_count

def main():
    """Command-line entry point for motion filtering."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Motion filtering for fMRI data')
    parser.add_argument('--filter', action='store_true', 
                      help='Run motion filtering pipeline')
    parser.add_argument('--input', type=str, default=None,
                      help='Input merged data CSV path')
    parser.add_argument('--output', type=str, default=None,
                      help='Output filtered data CSV path')
    parser.add_argument('--threshold', type=float, default=None,
                      help='FD threshold for exclusion')
    
    args = parser.parse_args()
    
    if args.filter:
        try:
            output_path, total, excluded = run_motion_filtering_pipeline(
                input_csv_path=args.input,
                output_csv_path=args.output,
                threshold=args.threshold
            )
            print(f"Motion filtering complete.")
            print(f"  Total subjects: {total}")
            print(f"  Excluded: {excluded}")
            print(f"  Output: {output_path}")
            print(f"  Exclusion log: {get_exclusion_log_path()}")
        except Exception as e:
            logger.error(f"Motion filtering failed: {e}")
            raise
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
