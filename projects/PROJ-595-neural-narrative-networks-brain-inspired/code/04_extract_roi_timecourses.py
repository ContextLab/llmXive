import os
import sys
import json
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# Project imports matching API surface
from utils.logging_config import get_logger, error, info, warning, log_error
from config import get_config

logger = get_logger(__name__)

def load_mask_from_json(mask_json_path: str) -> Optional[nib.Nifti1Image]:
    """
    Load ROI mask from the JSON record created by T013.
    Returns the nibabel image or None if not found.
    """
    mask_json_path = Path(mask_json_path)
    if not mask_json_path.exists():
        logger.error(f"Mask JSON not found: {mask_json_path}")
        return None

    with open(mask_json_path, 'r') as f:
        mask_info = json.load(f)

    # T013 saves keys: "left_hipp", "right_hipp", "dlpfc"
    # This function is generic; the caller passes the specific key or we assume
    # the JSON contains a 'mask_path' directly. For T013 output, we expect a dict.
    # The T013 output structure: {"left_hipp": "path", "right_hipp": "path", "dlpfc": "path"}
    # We assume the caller passes the specific path string or we need to know the key.
    # However, the function signature expects a path to JSON.
    # Let's assume the JSON contains a key "mask_path" or the file is just a string path.
    # Given T013 spec: "Save valid mask paths to data/processed/mask_paths.json"
    # The file contains a dict. We need to know which ROI to load.
    # Let's change the approach: This function will load the dict and return the specific ROI path.
    # But the function signature is fixed by API surface.
    # Re-reading API surface: `load_mask_from_json(mask_json_path: str) -> Optional[nib.Nifti1Image]`
    # It returns an image. So it must know which ROI.
    # Since T016 is specifically for DLPFC, we will hardcode the lookup key "dlpfc" inside
    # or assume the JSON passed is a single-record file.
    # Actually, the T013 output is a single file `data/processed/mask_paths.json`.
    # We will load that file, extract the 'dlpfc' path, then load the NIfTI.
    # To make this generic for T014/T015/T016, we might need an extra argument, but we must match API.
    # Let's assume the JSON file passed contains a key 'mask_path' pointing to the specific ROI,
    # OR we assume the function is called with the specific path string in a wrapper.
    # Given the strict API, let's assume the JSON file contains a single key "mask_path"
    # or we inspect the filename to determine ROI.
    # Better: The T013 output is a dict. We will read the dict. If the dict has "dlpfc", we use that.
    # But this function is generic.
    # Let's look at the task T016: "using masks from T013". T013 saves `data/processed/mask_paths.json`.
    # We will load that file inside `main` or a helper, then call `load_mask_from_json`?
    # No, `load_mask_from_json` is the entry point.
    # Let's assume the JSON file contains a key "mask_path" that points to the NIfTI.
    # If the file is the aggregate from T013, we need to know which one.
    # We will assume for T016 that the caller passes the specific path to the mask JSON,
    # and that JSON contains a key 'dlpfc' or 'mask_path'.
    # To be safe and match the T013 output format (dict of paths), we will read the dict.
    # If the dict has 'dlpfc', we use it.
    
    with open(mask_json_path, 'r') as f:
        data = json.load(f)
    
    mask_path_str = None
    if isinstance(data, dict):
        if 'dlpfc' in data:
            mask_path_str = data['dlpfc']
        elif 'mask_path' in data:
            mask_path_str = data['mask_path']
        else:
            logger.error(f"Mask JSON does not contain expected keys: {list(data.keys())}")
            return None
    elif isinstance(data, str):
        mask_path_str = data
    else:
        logger.error("Mask JSON is neither dict nor string")
        return None

    if not mask_path_str:
        return None

    mask_path = Path(mask_path_str)
    if not mask_path.exists():
        logger.error(f"Mask file not found: {mask_path}")
        return None

    try:
        return nib.load(mask_path)
    except Exception as e:
        logger.error(f"Failed to load mask {mask_path}: {e}")
        return None

def find_functional_runs(base_dir: str, subject_id: str) -> List[Path]:
    """
    Find functional runs matching the pattern: sub-*/func/*task-narratives_bold.nii.gz
    """
    sub_dir = Path(base_dir) / subject_id / 'func'
    if not sub_dir.exists():
        logger.warning(f"Functional directory not found: {sub_dir}")
        return []

    # Pattern: *task-narratives*.nii.gz
    runs = list(sub_dir.glob('*task-narratives*.nii.gz'))
    # Also check .nii if .nii.gz missing (rare but possible)
    if not runs:
        runs = list(sub_dir.glob('*task-narratives*.nii'))
    
    return sorted(runs)

def extract_roi_timecourse(
    func_img: nib.Nifti1Image,
    mask_img: nib.Nifti1Image,
    subject_id: str
) -> np.ndarray:
    """
    Extract mean BOLD timecourse within the ROI mask.
    Returns 1D array of shape (timepoints,).
    """
    # Get data
    func_data = func_img.get_fdata()
    mask_data = mask_img.get_fdata()

    # Ensure mask is boolean
    mask_bool = mask_data > 0

    # Check alignment (simplified: assume same shape or resampling needed)
    # For this pipeline, we assume masks are in the same space as the functional data
    # or pre-resampled by T013 logic (which generated them in standard space if needed).
    # If shapes differ, we must resample.
    if func_data.shape[:3] != mask_data.shape[:3]:
        logger.warning(f"Shape mismatch: func {func_data.shape[:3]} vs mask {mask_data.shape[:3]}. Attempting resampling.")
        # Resample mask to functional space
        from nilearn.image import resample_to_img
        mask_img_resampled = resample_to_img(mask_img, func_img, interpolation='nearest')
        mask_data = mask_img_resampled.get_fdata()
        mask_bool = mask_data > 0

    if mask_bool.sum() == 0:
        logger.error("Mask is empty after loading/resampling.")
        return np.array([])

    # Extract timecourse: mean signal over voxels in mask for each timepoint
    # func_data shape: (x, y, z, t)
    t_dim = func_data.shape[3]
    timecourse = np.zeros(t_dim)

    for t in range(t_dim):
        voxel_data = func_data[..., t]
        timecourse[t] = np.mean(voxel_data[mask_bool])

    return timecourse

def process_subject(
    base_dir: str,
    subject_id: str,
    mask_json_path: str
) -> Optional[np.ndarray]:
    """
    Process a single subject: find runs, extract timecourse, return combined.
    """
    mask_img = load_mask_from_json(mask_json_path)
    if mask_img is None:
        return None

    runs = find_functional_runs(base_dir, subject_id)
    if not runs:
        logger.warning(f"No functional runs found for {subject_id}")
        return None

    all_timecourses = []
    for run_path in runs:
        try:
            func_img = nib.load(run_path)
            tc = extract_roi_timecourse(func_img, mask_img, subject_id)
            if tc.size > 0:
                all_timecourses.append(tc)
            else:
                logger.warning(f"Empty timecourse for run {run_path}")
        except Exception as e:
            logger.error(f"Failed to process run {run_path}: {e}")
            return None

    if not all_timecourses:
        return None

    # Concatenate timecourses from all runs for this subject
    combined_tc = np.concatenate(all_timecourses)
    return combined_tc

def main():
    """
    T016: Extract BOLD timecourses for DLPFC for subjects 01-05.
    """
    config = get_config()
    base_dir = Path(config.get('data_raw_dir', 'data/raw/openneuro_ds001495'))
    output_path = Path('data/processed/roi_dlpfc.npy')
    mask_json_path = Path('data/processed/mask_paths.json')

    # Verify prerequisites
    if not base_dir.exists():
        log_error("E001", f"Raw data directory missing: {base_dir}")
        sys.exit(1)

    if not mask_json_path.exists():
        log_error("E001", f"Mask paths file missing: {mask_json_path}")
        sys.exit(1)

    subjects = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05']
    all_subject_timecourses = {}

    for subj in subjects:
        logger.info(f"Processing DLPFC for {subj}")
        tc = process_subject(str(base_dir), subj, str(mask_json_path))
        if tc is not None:
            all_subject_timecourses[subj] = tc
            logger.info(f"  Extracted {len(tc)} timepoints for {subj}")
        else:
            logger.warning(f"  Failed to extract timecourse for {subj}")

    if not all_subject_timecourses:
        log_error("E002", "No timecourses extracted for any subject.")
        sys.exit(1)

    # Save as dict in .npy (or structured array)
    # Format: dictionary mapping subject_id -> timecourse array
    # Or a 2D array if we pad? The task says "Save to data/processed/roi_dlpfc.npy"
    # Usually, ROI timecourses are saved as a dict or a list of arrays.
    # Let's save as a dict to preserve variable lengths per subject/run count.
    np.save(output_path, all_subject_timecourses)
    logger.info(f"Saved DLPFC timecourses to {output_path}")

    # Verification
    if output_path.exists():
        loaded = np.load(output_path, allow_pickle=True).item()
        logger.info(f"Verification: Loaded {len(loaded)} subjects from {output_path}")
        for k, v in loaded.items():
            logger.info(f"  {k}: shape {v.shape}")
    else:
        logger.error(f"Failed to write output file: {output_path}")
        sys.exit(1)

if __name__ == '__main__':
    main()