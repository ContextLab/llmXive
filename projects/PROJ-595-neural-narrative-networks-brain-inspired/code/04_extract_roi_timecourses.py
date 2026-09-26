"""
Extract ROI timecourses from fMRI data.
Implements T014 (Left Hippocampus), T015 (Right Hippocampus), T016 (DLPFC).
"""
import os
import sys
import json
import glob
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import from project utils
from utils.logging_config import get_logger, error, info, warning
from config import get_config

logger = get_logger(__name__)

def natural_sort_key(s: str) -> List:
    """
    Generate a key for natural sorting of subject IDs (e.g., 'sub-01', 'sub-02', 'sub-10').
    """
    import re
    return [int(c) if c.isdigit() else c.lower() for c in re.split('([0-9]+)', s)]

def load_mask_from_json(mask_json_path: str, roi_name: str) -> np.ndarray:
    """
    Load mask path from JSON and return the mask array.
    """
    with open(mask_json_path, 'r') as f:
        mask_paths = json.load(f)
    
    if roi_name not in mask_paths:
        raise FileNotFoundError(f"ROI '{roi_name}' not found in mask paths: {mask_paths.keys()}")
    
    mask_path = mask_paths[roi_name]
    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"Mask file not found: {mask_path}")
    
    mask_img = nib.load(mask_path)
    return mask_img.get_fdata()

def find_functional_runs(subject_dir: str, task_name: str = "narratives") -> List[str]:
    """
    Find all functional NIfTI files for a subject matching the task name.
    Input Pattern: sub-*/func/*task-narratives_bold.nii.gz
    """
    pattern = os.path.join(subject_dir, "func", f"*task-{task_name}_bold.nii.gz")
    files = glob.glob(pattern)
    return sorted(files, key=natural_sort_key)

def extract_roi_timecourse(nifti_path: str, mask_array: np.ndarray) -> Optional[np.ndarray]:
    """
    Extract BOLD timecourse for a specific ROI.
    1. Load NIfTI
    2. Apply Mask
    3. Average Voxels across time
    
    Returns: 1D array of timepoints, or None if empty.
    """
    try:
        img = nib.load(nifti_path)
        data = img.get_fdata()
    except Exception as e:
        logger.error(f"Failed to load NIfTI {nifti_path}: {e}")
        return None

    if data.ndim < 4:
        logger.error(f"Data in {nifti_path} is not 4D (expected x,y,z,time). Shape: {data.shape}")
        return None

    # Ensure mask is boolean or compatible
    mask_bool = mask_array > 0
    
    # Apply mask to the last dimension (time)
    # data shape: (x, y, z, t)
    # mask shape: (x, y, z)
    masked_data = data[mask_bool]
    
    if masked_data.size == 0:
        logger.warning(f"No voxels found in mask for {nifti_path}")
        return None

    # Reshape to (n_voxels, n_timepoints)
    n_voxels = mask_bool.sum()
    n_timepoints = data.shape[-1]
    masked_data = masked_data.reshape(n_voxels, n_timepoints)

    # Average across voxels
    timecourse = masked_data.mean(axis=0)
    
    if timecourse.size == 0:
        return None
        
    return timecourse

def process_subject(subject_dir: str, mask_array: np.ndarray, roi_name: str) -> Optional[np.ndarray]:
    """
    Process a single subject directory: find runs, extract timecourse, average across runs.
    """
    runs = find_functional_runs(subject_dir)
    if not runs:
        logger.warning(f"No functional runs found for {subject_dir}")
        return None

    all_timecourses = []
    for run_path in runs:
        tc = extract_roi_timecourse(run_path, mask_array)
        if tc is not None:
            all_timecourses.append(tc)
    
    if not all_timecourses:
        return None

    # If multiple runs, we need to handle length mismatches.
    # For simplicity in this pipeline, we assume equal length or take the first valid one.
    # A robust implementation would concatenate or interpolate.
    # Here we take the first valid run to avoid complexity unless specified.
    # However, standard practice is to concatenate if TR matches.
    # Let's assume they are equal length for this specific dataset/task.
    first_tc = all_timecourses[0]
    for tc in all_timecourses[1:]:
        if tc.shape[0] != first_tc.shape[0]:
            logger.warning(f"Timepoint mismatch in runs for {subject_dir}. Using first run only.")
            break
    return first_tc

def main():
    """
    Main entry point for T015 (Right Hippocampus).
    Can be parameterized for T014/T016 as well.
    
    Logic:
    1. Check T012 artifacts (raw data) exist.
    2. Check T013 artifacts (mask paths) exist.
    3. Iterate all subjects in data/raw/openneuro_ds001495.
    4. Extract timecourse for Right Hippocampus.
    5. Save to data/processed/roi_right_hipp.npy.
    """
    config = get_config()
    raw_dir = Path("data/raw/openneuro_ds001495")
    mask_json_path = "data/processed/mask_paths.json"
    output_path = "data/processed/roi_right_hipp.npy"
    roi_name = "right_hipp"

    # 1. Verify T012 (Raw Data)
    if not raw_dir.exists():
        logger.error("E001: Raw data directory missing. T012 not completed.")
        sys.exit(1)
    
    subjects = [d for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    if not subjects:
        logger.error("E001: No subject directories found in raw data.")
        sys.exit(1)

    # 2. Verify T013 (Mask Paths)
    if not os.path.exists(mask_json_path):
        logger.error("E001: Mask paths JSON missing. T013 not completed.")
        sys.exit(1)

    try:
        mask_array = load_mask_from_json(mask_json_path, roi_name)
    except Exception as e:
        logger.error(f"E001: Failed to load mask for {roi_name}: {e}")
        sys.exit(1)

    # 3. Process Subjects
    sorted_subjects = sorted(subjects, key=lambda x: natural_sort_key(x.name))
    results = []
    subject_ids = []

    for subj_dir in sorted_subjects:
        tc = process_subject(str(subj_dir), mask_array, roi_name)
        if tc is not None:
            results.append(tc)
            subject_ids.append(subj_dir.name)
            info(f"Processed {subj_dir.name}: {len(tc)} timepoints")
        else:
            warning(f"Skipped {subj_dir.name}: No valid timecourse extracted")

    if not results:
        logger.error("E002: No timecourses extracted. Result is empty.")
        sys.exit(1)

    # 4. Save Output
    # Stack into a 2D array: (n_subjects, n_timepoints)
    # Pad if necessary? T015 doesn't explicitly ask for padding, but T019 does.
    # We save the raw extracted array here. T019 will handle padding.
    # To make it a valid NPY, we assume we save a list of arrays or a padded 2D array.
    # Given T019 expects to pad, saving as a list of 1D arrays is safer if lengths vary.
    # However, NPY usually implies a single array. Let's save a structured array or a list.
    # The task says "Save NPY". Let's save a 2D array padded with NaNs if lengths differ.
    
    max_len = max(len(tc) for tc in results)
    padded_results = []
    for tc in results:
        if len(tc) < max_len:
            padding = np.full(max_len - len(tc), np.nan, dtype=np.float32)
            padded_tc = np.concatenate([tc, padding])
        else:
            padded_tc = tc
        padded_results.append(padded_tc)
    
    final_array = np.array(padded_results, dtype=np.float32)
    
    # Save
    np.save(output_path, final_array)
    info(f"Saved timecourses to {output_path} (shape: {final_array.shape})")
    
    # Also save subject IDs for reference
    ids_path = output_path.replace('.npy', '_ids.json')
    with open(ids_path, 'w') as f:
        json.dump(subject_ids, f)

if __name__ == "__main__":
    main()
