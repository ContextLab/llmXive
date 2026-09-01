"""
Motion analysis utilities for fMRI preprocessing.

Implements Mean Frame Displacement (Mean FD) calculation from
realignment parameters and subject exclusion logic based on
configurable thresholds.
"""

import csv
import os
import logging
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
import nibabel as nib

from code.config import get_config
from code.data.paths import get_raw_path, get_processed_path, ensure_dir
from code.utils.logging import log_exclusion, get_exclusion_log_path

logger = logging.getLogger(__name__)

def calculate_mean_fd(realignment_params: np.ndarray) -> float:
    """
    Calculate Mean Frame Displacement (Mean FD) from realignment parameters.
    
    Uses the Power et al. (2012) definition of FD:
    FD = |Δx| + |Δy| + |Δz| + |Δα| + |Δβ| + |Δγ|
    where the angular displacements are converted to mm assuming a
    radius of 50mm.
    
    Args:
        realignment_params: numpy array of shape (n_timepoints, 6) containing
            [x, y, z, pitch, roll, yaw] for each timepoint.
            
    Returns:
        float: Mean FD across all timepoints.
    """
    if realignment_params.shape[1] != 6:
        raise ValueError(f"Expected 6 realignment parameters, got {realignment_params.shape[1]}")
    
    # Calculate displacements (differences between consecutive timepoints)
    displacements = np.diff(realignment_params, axis=0)
    
    # Convert angular displacements to mm (assuming 50mm radius)
    # Angles are typically in radians
    angular_displacements = displacements[:, 3:] * 50.0  # 3 columns: pitch, roll, yaw
    translational_displacements = displacements[:, :3]   # 3 columns: x, y, z
    
    # Calculate FD for each timepoint (Power et al., 2012)
    fd_per_timepoint = np.abs(translational_displacements).sum(axis=1) + \
                       np.abs(angular_displacements).sum(axis=1)
    
    # Mean FD (note: we lose one timepoint due to differencing)
    mean_fd = np.mean(fd_per_timepoint)
    
    return float(mean_fd)

def load_motion_params_from_nifti(nifti_path: str) -> np.ndarray:
    """
    Load realignment parameters from a NIfTI file.
    
    Assumes the NIfTI file contains realignment parameters in the
    header's 'descrip' field or as a separate .mat/.txt file with
    the same base name.
    
    Args:
        nifti_path: Path to the NIfTI file containing motion parameters.
        
    Returns:
        numpy.ndarray: Array of shape (n_timepoints, 6) with realignment parameters.
        
    Raises:
        FileNotFoundError: If motion parameters cannot be found.
        ValueError: If motion parameters have incorrect format.
    """
    base_name = os.path.splitext(nifti_path)[0]
    
    # Try to find motion parameters in various locations
    possible_paths = [
        f"{base_name}_rp.txt",
        f"{base_name}_rp.mat",
        f"{base_name}_realign_params.txt",
        f"{os.path.join(os.path.dirname(base_name), 'realign', os.path.basename(base_name))}_rp.txt",
    ]
    
    # Also check for parameters embedded in the NIfTI header
    try:
        img = nib.load(nifti_path)
        # Check if motion parameters are stored in the header
        if hasattr(img, 'header') and 'descrip' in img.header:
            descr = img.header['descrip']
            if isinstance(descr, bytes):
                descr = descr.decode('utf-8')
            # If descr contains comma-separated numbers, try to parse them
            if ',' in descr or '\n' in descr:
                try:
                    params = np.loadtxt(os.path.join(os.path.dirname(nifti_path), descr.split('\n')[0].strip()))
                    if params.ndim == 1:
                        params = params.reshape(-1, 6)
                    return params
                except (ValueError, IOError):
                    pass
    except Exception as e:
        logger.debug(f"Could not extract motion params from NIfTI header: {e}")
    
    # Try to load from separate file
    for path in possible_paths:
        if os.path.exists(path):
            try:
                # Try loading as text file
                params = np.loadtxt(path)
                if params.ndim == 1:
                    params = params.reshape(-1, 6)
                if params.shape[1] == 6:
                    return params
            except Exception:
                continue
            
            # Try loading as MATLAB file if scipy.io is available
            try:
                import scipy.io
                mat_data = scipy.io.loadmat(path)
                # Look for common variable names
                for key in mat_data:
                    if key.startswith('__') or key == 'params':
                        continue
                    if hasattr(mat_data[key], 'shape') and len(mat_data[key].shape) >= 2:
                        params = mat_data[key]
                        if params.shape[1] == 6:
                            return params
                # If we found a matrix, return it
                for key in mat_data:
                    if not key.startswith('__'):
                        params = mat_data[key]
                        if hasattr(params, 'shape') and len(params.shape) >= 2:
                            return params
                break
            except ImportError:
                logger.warning("scipy.io not available, cannot load .mat files")
                break
            except Exception:
                continue
    
    raise FileNotFoundError(
        f"Could not find motion parameters for {nifti_path}. "
        f"Expected one of: {', '.join(possible_paths)}"
    )

def check_motion_exclusion(mean_fd: float, threshold: Optional[float] = None) -> Tuple[bool, str]:
    """
    Check if a subject should be excluded based on Mean FD.
    
    Args:
        mean_fd: Calculated Mean FD for the subject.
        threshold: FD threshold for exclusion. If None, uses config value.
        
    Returns:
        Tuple[bool, str]: (should_exclude, reason)
    """
    if threshold is None:
        config = get_config()
        threshold = config.get('FD_threshold', 0.2)
    
    if mean_fd > threshold:
        return True, f"Mean_FD ({mean_fd:.4f}) exceeds threshold ({threshold})"
    
    return False, ""

def generate_exclusion_log(excluded_subjects: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """
    Generate a CSV log of excluded subjects.
    
    Args:
        excluded_subjects: List of dicts with keys: Subject_ID, Exclusion_Reason, Mean_FD.
        output_path: Path to write the exclusion log. If None, uses default path.
        
    Returns:
        str: Path to the generated exclusion log.
    """
    if output_path is None:
        output_path = get_exclusion_log_path()
    
    ensure_dir(os.path.dirname(output_path))
    
    fieldnames = ['Subject_ID', 'Exclusion_Reason', 'Mean_FD']
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for subject in excluded_subjects:
            writer.writerow({
                'Subject_ID': subject['Subject_ID'],
                'Exclusion_Reason': subject['Exclusion_Reason'],
                'Mean_FD': f"{subject['Mean_FD']:.6f}"
            })
    
    logger.info(f"Exclusion log written to {output_path} with {len(excluded_subjects)} entries")
    return output_path

def process_subject_motion(subject_id: str, nifti_path: str, threshold: Optional[float] = None) -> Dict[str, Any]:
    """
    Process a single subject's motion parameters and determine exclusion status.
    
    Args:
        subject_id: Subject identifier.
        nifti_path: Path to the subject's NIfTI file.
        threshold: FD threshold for exclusion.
        
    Returns:
        Dict with keys: Subject_ID, Mean_FD, Should_Exclude, Exclusion_Reason
    """
    try:
        # Load motion parameters
        realignment_params = load_motion_params_from_nifti(nifti_path)
        
        # Calculate Mean FD
        mean_fd = calculate_mean_fd(realignment_params)
        
        # Check exclusion
        should_exclude, reason = check_motion_exclusion(mean_fd, threshold)
        
        return {
            'Subject_ID': subject_id,
            'Mean_FD': mean_fd,
            'Should_Exclude': should_exclude,
            'Exclusion_Reason': reason if should_exclude else ""
        }
        
    except FileNotFoundError as e:
        logger.error(f"Motion parameters not found for {subject_id}: {e}")
        return {
            'Subject_ID': subject_id,
            'Mean_FD': None,
            'Should_Exclude': True,
            'Exclusion_Reason': f"Motion parameters not found: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error processing motion for {subject_id}: {e}")
        return {
            'Subject_ID': subject_id,
            'Mean_FD': None,
            'Should_Exclude': True,
            'Exclusion_Reason': f"Error processing motion: {str(e)}"
        }

def run_motion_filtering_pipeline(subject_list_path: str, output_dir: Optional[str] = None) -> Tuple[List[str], int]:
    """
    Run the motion filtering pipeline for a list of subjects.
    
    Args:
        subject_list_path: Path to file containing subject IDs (one per line).
        output_dir: Directory to write exclusion log. If None, uses default.
        
    Returns:
        Tuple[List[str], int]: (excluded_subject_ids, total_processed)
    """
    config = get_config()
    fd_threshold = config.get('FD_threshold', 0.2)
    
    # Read subject list
    with open(subject_list_path, 'r') as f:
        subject_ids = [line.strip() for line in f if line.strip()]
    
    logger.info(f"Processing motion for {len(subject_ids)} subjects (FD threshold: {fd_threshold})")
    
    excluded_subjects = []
    excluded_ids = []
    
    for subject_id in subject_ids:
        # Construct path to NIfTI file
        raw_path = get_raw_path()
        nifti_path = os.path.join(raw_path, 'HCP_1200', f"{subject_id}_rest.nii.gz")
        
        # If exact path not found, try variations
        if not os.path.exists(nifti_path):
            # Try without .gz
            nifti_path = os.path.join(raw_path, 'HCP_1200', f"{subject_id}_rest.nii")
            if not os.path.exists(nifti_path):
                # Try in subdirectory
                nifti_path = os.path.join(raw_path, 'HCP_1200', 'rest', f"{subject_id}_rest.nii.gz")
                if not os.path.exists(nifti_path):
                    nifti_path = os.path.join(raw_path, 'HCP_1200', 'rest', f"{subject_id}_rest.nii")
        
        if not os.path.exists(nifti_path):
            logger.warning(f"NIfTI file not found for {subject_id}: {nifti_path}")
            # Try to find any NIfTI file for this subject
            search_dir = os.path.join(raw_path, 'HCP_1200')
            if os.path.exists(search_dir):
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        if subject_id in file and (file.endswith('.nii') or file.endswith('.nii.gz')):
                            nifti_path = os.path.join(root, file)
                            logger.info(f"Found alternative NIfTI for {subject_id}: {nifti_path}")
                            break
                    if os.path.exists(nifti_path):
                        break
        
        if not os.path.exists(nifti_path):
            logger.error(f"Could not find NIfTI file for {subject_id}")
            excluded_subjects.append({
                'Subject_ID': subject_id,
                'Exclusion_Reason': "NIfTI file not found",
                'Mean_FD': None
            })
            excluded_ids.append(subject_id)
            continue
        
        # Process motion
        result = process_subject_motion(subject_id, nifti_path, fd_threshold)
        
        if result['Should_Exclude']:
            excluded_subjects.append({
                'Subject_ID': subject_id,
                'Exclusion_Reason': result['Exclusion_Reason'],
                'Mean_FD': result['Mean_FD']
            })
            excluded_ids.append(subject_id)
            log_exclusion(
                subject_id=subject_id,
                reason=result['Exclusion_Reason'],
                metric_name="Mean_FD",
                metric_value=result['Mean_FD']
            )
        else:
            logger.debug(f"Subject {subject_id} passed motion filter (Mean_FD: {result['Mean_FD']:.4f})")
    
    # Write exclusion log
    output_path = os.path.join(output_dir, 'exclusion_log.csv') if output_dir else None
    generate_exclusion_log(excluded_subjects, output_path)
    
    logger.info(f"Motion filtering complete: {len(excluded_ids)} of {len(subject_ids)} subjects excluded")
    return excluded_ids, len(subject_ids)

def main():
    """Command-line entry point for motion filtering."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Filter subjects based on motion parameters")
    parser.add_argument(
        "--subject-list",
        type=str,
        default="data/raw/HCP_1200/subject_list.txt",
        help="Path to file containing subject IDs"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for exclusion log (default: data/processed/)"
    )
    parser.add_argument(
        "--fd-threshold",
        type=float,
        default=None,
        help="FD threshold (default: from config)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Run pipeline
    excluded_ids, total = run_motion_filtering_pipeline(
        args.subject_list,
        args.output_dir
    )
    
    print(f"Motion filtering complete:")
    print(f"  Total subjects: {total}")
    print(f"  Excluded: {len(excluded_ids)}")
    print(f"  Retained: {total - len(excluded_ids)}")
    
    if excluded_ids:
        print(f"  Excluded subjects: {', '.join(excluded_ids[:10])}{'...' if len(excluded_ids) > 10 else ''}")
    
    return 0 if len(excluded_ids) < total else 1

if __name__ == "__main__":
    exit(main())