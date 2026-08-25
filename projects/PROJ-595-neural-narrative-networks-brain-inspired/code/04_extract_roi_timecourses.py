"""
Extract BOLD timecourses for ROIs from fMRI data.

This script extracts timecourses for specific ROIs (e.g., DLPFC) from fMRI data
using masks defined in data/processed/mask_paths.json.

Requirements:
- T013: Masks must be present in data/processed/mask_paths.json
- data/raw/ must contain the OpenNeuro ds001495 dataset

Outputs:
- data/processed/roi_dlpfc.npy: Extracted BOLD timecourses for DLPFC
"""

import os
import sys
import json
import numpy as np
import nibabel as nib
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, error, info, warning
from utils.checksums import compute_sha256
from config import get_config

# Configure logger
logger = get_logger(__name__)


def load_mask_from_json(mask_json_path: str) -> dict:
    """
    Load mask paths from JSON file.

    Args:
        mask_json_path: Path to mask_paths.json

    Returns:
        Dictionary with mask paths for each ROI

    Raises:
        FileNotFoundError: If mask JSON file doesn't exist
        KeyError: If required ROI keys are missing
    """
    try:
        with open(mask_json_path, 'r') as f:
            mask_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Mask JSON file not found: {mask_json_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in mask file: {e}")

    # Verify required keys
    required_keys = ['left_hipp', 'right_hipp', 'dlpfc']
    for key in required_keys:
        if key not in mask_data:
            raise KeyError(f"Missing required key '{key}' in mask JSON")

    return mask_data


def find_functional_runs(subject_dir: Path) -> list:
    """
    Find functional runs in a subject's directory.

    Args:
        subject_dir: Path to subject directory

    Returns:
        List of functional run file paths
    """
    func_runs = []

    # Look for functional data in standard OpenNeuro structure
    # Pattern: sub-<label>/func/sub-<label>_task-<label>_run-<label>_space-<label>_bold.nii.gz
    func_dir = subject_dir / 'func'
    if not func_dir.exists():
        return func_runs

    for func_file in func_dir.glob('*bold.nii.gz'):
        func_runs.append(func_file)

    return sorted(func_runs)


def extract_roi_timecourse(func_img: nib.Nifti1Image, mask_img: nib.Nifti1Image) -> np.ndarray:
    """
    Extract mean BOLD timecourse from a functional image using a mask.

    Args:
        func_img: Functional image (4D NIfTI)
        mask_img: Binary mask image (3D NIfTI)

    Returns:
        1D array of mean BOLD signal over time
    """
    # Get data arrays
    func_data = func_img.get_fdata()
    mask_data = mask_img.get_fdata()

    # Ensure mask is binary
    mask_binary = (mask_data > 0).astype(bool)

    # Get number of timepoints
    if func_data.ndim == 4:
        n_timepoints = func_data.shape[3]
    else:
        raise ValueError(f"Expected 4D functional image, got {func_data.ndim}D")

    # Extract timecourse
    timecourse = np.zeros(n_timepoints)
    n_voxels = 0

    for t in range(n_timepoints):
        # Get 3D volume at timepoint t
        volume = func_data[:, :, :, t]

        # Apply mask and compute mean
        masked_values = volume[mask_binary]
        if len(masked_values) > 0:
            timecourse[t] = np.mean(masked_values)
            n_voxels += len(masked_values)

    if n_voxels == 0:
        raise ValueError("No voxels found in mask")

    return timecourse


def process_subject(subject_dir: Path, mask_path: Path, output_dir: Path, roi_name: str) -> dict:
    """
    Process a single subject's fMRI data for a specific ROI.

    Args:
        subject_dir: Path to subject directory
        mask_path: Path to ROI mask file
        output_dir: Directory to save output
        roi_name: Name of the ROI (e.g., 'dlpfc')

    Returns:
        Dictionary with processing results
    """
    results = {
        'subject_id': subject_dir.name,
        'roi': roi_name,
        'success': False,
        'error': None,
        'timepoints': 0,
        'output_path': None
    }

    try:
        # Load mask
        if not mask_path.exists():
            raise FileNotFoundError(f"Mask file not found: {mask_path}")

        mask_img = nib.load(str(mask_path))

        # Find functional runs
        func_runs = find_functional_runs(subject_dir)
        if not func_runs:
            raise ValueError("No functional runs found")

        # Process each run and combine
        all_timecourses = []
        for func_run in func_runs:
            try:
                func_img = nib.load(str(func_run))
                timecourse = extract_roi_timecourse(func_img, mask_img)
                all_timecourses.append(timecourse)
            except Exception as e:
                logger.warning(f"Failed to process {func_run}: {e}")
                continue

        if not all_timecourses:
            raise ValueError("No valid timecourses extracted")

        # Combine timecourses (concatenate)
        combined_timecourse = np.concatenate(all_timecourses)

        # Save output
        output_file = output_dir / f"{subject_dir.name}_{roi_name}.npy"
        np.save(str(output_file), combined_timecourse)

        results['success'] = True
        results['timepoints'] = len(combined_timecourse)
        results['output_path'] = str(output_file)

        logger.info(f"Successfully processed {subject_dir.name} for {roi_name}: "
                   f"{len(combined_timecourse)} timepoints")

    except Exception as e:
        results['error'] = str(e)
        logger.error(f"Failed to process {subject_dir.name} for {roi_name}: {e}")

    return results


def main():
    """
    Main function to extract DLPFC timecourses from all subjects.
    """
    config = get_config()
    logger.info("Starting DLPFC timecourse extraction")

    # Define paths
    project_root = Path(__file__).parent.parent
    data_raw = project_root / 'data' / 'raw' / 'openneuro_ds001495'
    mask_json = project_root / 'data' / 'processed' / 'mask_paths.json'
    output_dir = project_root / 'data' / 'processed'

    # Check if data exists
    if not data_raw.exists():
        error("E001", f"Data directory not found: {data_raw}")
        sys.exit(1)

    # Check if mask file exists
    if not mask_json.exists():
        error("E001", f"Mask file not found: {mask_json}. Run T013 first.")
        sys.exit(1)

    # Load mask paths
    try:
        mask_data = load_mask_from_json(str(mask_json))
    except (FileNotFoundError, KeyError, ValueError) as e:
        error("E001", f"Failed to load masks: {e}")
        sys.exit(1)

    dlpfc_mask = Path(mask_data['dlpfc'])
    if not dlpfc_mask.exists():
        error("E001", f"DLPFC mask not found: {dlpfc_mask}")
        sys.exit(1)

    # Find all subjects
    subjects = sorted([d for d in data_raw.iterdir() if d.is_dir() and d.name.startswith('sub-')])

    if not subjects:
        error("E002", "No subject directories found in data/raw/openneuro_ds001495")
        sys.exit(1)

    logger.info(f"Found {len(subjects)} subjects to process")

    # Process each subject
    all_results = []
    success_count = 0

    for subject_dir in subjects:
        result = process_subject(subject_dir, dlpfc_mask, output_dir, 'dlpfc')
        all_results.append(result)
        if result['success']:
            success_count += 1

    # Check if we have any successful extractions
    if success_count == 0:
        error("E002", "No DLPFC timecourses were successfully extracted")
        sys.exit(1)

    logger.info(f"Successfully extracted DLPFC timecourses for {success_count}/{len(subjects)} subjects")

    # Combine all timecourses into a single file
    # Format: list of (subject_id, timecourse)
    combined_data = []
    for result in all_results:
        if result['success']:
          output_path = Path(result['output_path'])
          if output_path.exists():
              timecourse = np.load(str(output_path))
              combined_data.append({
                  'subject_id': result['subject_id'],
                  'timecourse': timecourse
              })

    if not combined_data:
        error("E002", "No valid combined data to save")
        sys.exit(1)

    # Save combined data as a structured array or list
    # We'll save as a dictionary with subject IDs as keys
    combined_dict = {item['subject_id']: item['timecourse'] for item in combined_data}

    output_file = output_dir / 'roi_dlpfc.npy'
    np.save(str(output_file), combined_dict)

    logger.info(f"Saved combined DLPFC timecourses to {output_file}")

    # Compute checksum
    checksum = compute_sha256(str(output_file))
    logger.info(f"Output file checksum: {checksum}")

    return 0


if __name__ == '__main__':
    sys.exit(main())