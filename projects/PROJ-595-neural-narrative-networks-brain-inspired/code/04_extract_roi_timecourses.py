import os
import sys
import json
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from project utilities
from utils.logging_config import get_logger, log_error, info, error, warning
from utils.checksums import compute_sha256
from config import get_config

logger = get_logger(__name__)

def load_mask_from_json(mask_json_path: str) -> Optional[nib.Nifti1Image]:
    """
    Load a mask image path from the mask_paths.json file.
    Returns the nibabel image object or None if not found.
    """
    if not os.path.exists(mask_json_path):
        error(f"Mask paths file not found: {mask_json_path}")
        return None

    with open(mask_json_path, 'r') as f:
        mask_data = json.load(f)

    dlpfc_path = mask_data.get('dlpfc')
    if not dlpfc_path or not os.path.exists(dlpfc_path):
        error(f"DLPFC mask file not found at path specified in JSON: {dlpfc_path}")
        return None

    try:
        img = nib.load(dlpfc_path)
        logger.info(f"Successfully loaded DLPFC mask from {dlpfc_path}")
        return img
    except Exception as e:
        error(f"Failed to load DLPFC mask image: {e}")
        return None

def find_functional_runs(subject_dir: Path) -> List[Path]:
    """
    Find all functional runs (bold.nii.gz) for a given subject directory.
    Expects structure: sub-*/func/sub-*_task-narratives_bold.nii.gz
    """
    func_dir = subject_dir / 'func'
    if not func_dir.exists():
        return []

    # Pattern matching for OpenNeuro ds001495 style
    runs = list(func_dir.glob('*_task-narratives_bold.nii.gz'))
    # Also check for .nii if gz is missing
    if not runs:
        runs = list(func_dir.glob('*_task-narratives_bold.nii'))
    
    logger.info(f"Found {len(runs)} functional runs for subject {subject_dir.name}")
    return sorted(runs)

def extract_roi_timecourse(
    bold_path: Path, 
    mask_img: nib.Nifti1Image
) -> Optional[np.ndarray]:
    """
    Extract mean BOLD timecourse from a single 4D fMRI run using the provided mask.
    Returns a 1D numpy array of shape (timepoints,).
    """
    try:
        bold_img = nib.load(bold_path)
        bold_data = bold_img.get_fdata()
    except Exception as e:
        error(f"Failed to load BOLD image {bold_path}: {e}")
        return None

    if bold_data.ndim != 4:
        error(f"BOLD image {bold_path} is not 4D (got {bold_data.ndim}D)")
        return None

    mask_data = mask_img.get_fdata()
    # Ensure mask is binary (0 or 1)
    mask_binary = (mask_data > 0).astype(bool)

    if not np.any(mask_binary):
        error(f"Mask for {bold_path} is empty (no voxels selected)")
        return None

    # Apply mask and compute mean across voxels for each timepoint
    # Shape: (x, y, z, t) -> select voxels -> (n_voxels, t) -> mean axis 0 -> (t,)
    masked_data = bold_data[mask_binary, :]
    if masked_data.shape[0] == 0:
        error(f"No overlapping voxels between mask and BOLD data for {bold_path}")
        return None

    mean_timecourse = np.mean(masked_data, axis=0)
    logger.info(f"Extracted timecourse of length {len(mean_timecourse)} from {bold_path.name}")
    return mean_timecourse

def process_subject(
    subject_dir: Path,
    mask_img: nib.Nifti1Image,
    output_dir: Path
) -> bool:
    """
    Process a single subject: find runs, extract DLPFC timecourse, save to .npy.
    Returns True if successful, False otherwise.
    """
    run_paths = find_functional_runs(subject_dir)
    if not run_paths:
        warning(f"No functional runs found for subject {subject_dir.name}, skipping.")
        return False

    all_timecourses = []
    for run_path in run_paths:
        tc = extract_roi_timecourse(run_path, mask_img)
        if tc is not None:
            all_timecourses.append(tc)

    if not all_timecourses:
        error(f"No valid timecourses extracted for subject {subject_dir.name}")
        return False

    # Concatenate timecourses from all runs (or average them if preferred, 
    # but concatenation preserves temporal structure for event mapping)
    # For this task, we will concatenate and save the combined array per subject.
    combined_tc = np.concatenate(all_timecourses)
    
    output_path = output_dir / f"sub-{subject_dir.name}_dlpfc.npy"
    try:
        np.save(output_path, combined_tc)
        logger.info(f"Saved DLPFC timecourse for {subject_dir.name} to {output_path}")
        return True
    except Exception as e:
        error(f"Failed to save timecourse for {subject_dir.name}: {e}")
        return False

def main():
    """
    Main entry point for extracting DLPFC timecourses.
    Reads mask paths from data/processed/mask_paths.json.
    Reads raw data from data/raw/openneuro_ds001495/.
    Saves outputs to data/processed/roi_dlpfc.npy (aggregated across subjects).
    """
    config = get_config()
    raw_dir = Path("data/raw/openneuro_ds001495")
    mask_json = Path("data/processed/mask_paths.json")
    output_dir = Path("data/processed")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check dependencies
    if not raw_dir.exists():
        error(f"Raw data directory missing: {raw_dir}. Did T012 run?")
        sys.exit(1)

    if not mask_json.exists():
        error(f"Mask paths JSON missing: {mask_json}. Did T013 run?")
        sys.exit(1)

    # Load mask
    mask_img = load_mask_from_json(str(mask_json))
    if mask_img is None:
        error("Failed to load DLPFC mask. Cannot proceed.")
        sys.exit(1)

    # Find subjects
    subjects = sorted([d for d in raw_dir.iterdir() if d.name.startswith('sub-') and d.is_dir()])
    if not subjects:
        error(f"No subjects found in {raw_dir}")
        sys.exit(1)

    logger.info(f"Processing {len(subjects)} subjects for DLPFC extraction.")

    # Collect all timecourses with subject metadata
    # We will save a single .npy file containing a structured array or a list of tuples?
    # The task requires saving to `data/processed/roi_dlpfc.npy`.
    # To be compatible with T014/T015 (which likely saved single arrays per subject),
    # we will save a dictionary or a structured array containing all subjects.
    # However, the task description says "Save to data/processed/roi_dlpfc.npy".
    # Let's save a structured array: [(subject_id, timepoints), ...] or a dict.
    # Given the downstream T017 combines them into a CSV, a dict {sub_id: array} is useful.
    
    results = {}
    success_count = 0

    for subj_dir in subjects:
        success = process_subject(subj_dir, mask_img, output_dir)
        if success:
            subj_id = subj_dir.name
            # Load the saved file to aggregate in memory for the final combined file
            # Or we can just read the saved file later. Let's save the per-subject file
            # and then load them all into a combined structure for the final output.
            # Actually, the task says "Save to data/processed/roi_dlpfc.npy". 
            # T014/T015 save per-subject? No, T014 says "Save to data/processed/roi_left_hipp.npy".
            # This implies a single file for the whole project? Or per subject?
            # Looking at T017: "Combine extracted timecourses into a single ... roi_timecourses.csv".
            # It's safer to save per-subject files named `sub-X_dlpfc.npy` and then T017 loads them.
            # BUT the task text says "Save to data/processed/roi_dlpfc.npy".
            # Let's follow the literal instruction: Save a single file containing all data.
            # We'll store a dict {subject_id: np.array} inside the .npy file.
            pass
        else:
            warning(f"Failed to process {subj_dir.name}")

    # Re-process to populate the single output file as requested
    all_data = {}
    for subj_dir in subjects:
        run_paths = find_functional_runs(subj_dir)
        if not run_paths:
            continue
        
        all_tcs = []
        for run_path in run_paths:
            tc = extract_roi_timecourse(run_path, mask_img)
            if tc is not None:
                all_tcs.append(tc)
        
        if all_tcs:
            combined = np.concatenate(all_tcs)
            all_data[subj_dir.name] = combined

    if not all_data:
        error("No DLPFC timecourses could be extracted for any subject.")
        sys.exit(1)

    # Save as a Python dictionary in .npz (which is standard for dict-like numpy data)
    # But task says .npy. .npy can only hold one array. 
    # We will save a structured array or object array.
    # Object array is safest for variable-length timecourses.
    subj_ids = np.array(list(all_data.keys()), dtype=object)
    timecourses = np.array(list(all_data.values()), dtype=object)
    
    # Create a structured array to save as .npy
    # Actually, just saving the dict as a pickle-compatible object array is fine.
    # Or, we save a 2D array with padding? No, variable lengths.
    # Let's save a tuple (subj_ids, timecourses) as an object array.
    output_array = np.array([subj_ids, timecourses], dtype=object)
    output_file = output_dir / "roi_dlpfc.npy"
    
    try:
        np.save(output_file, output_array)
        logger.info(f"Saved DLPFC timecourses for {len(all_data)} subjects to {output_file}")
        
        # Verify integrity
        checksum = compute_sha256(output_file)
        logger.info(f"Checksum for {output_file}: {checksum}")
        
    except Exception as e:
        error(f"Failed to save DLPFC timecourses: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()