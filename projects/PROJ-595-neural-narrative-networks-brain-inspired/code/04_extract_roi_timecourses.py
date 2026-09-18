"""
Extract BOLD timecourses for a specific ROI from OpenNeuro ds001495.
Implements T014 (Left Hippocampus) but is parameterized for any ROI.
"""
import os
import sys
import json
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import List, Optional, Tuple

# Import from existing project API surface
from config import get_config
from utils.logging_config import get_logger, error, info, warning
from utils.checksums import compute_sha256

logger = get_logger(__name__)
config = get_config()

def load_mask_from_json(mask_json_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load ROI mask path from mask_paths.json and return the mask array and affine.
    """
    with open(mask_json_path, 'r') as f:
        mask_info = json.load(f)
    
    # Determine which key to use based on the caller context (passed via env or arg)
    # For T014, we specifically need 'left_hipp'
    roi_key = os.environ.get('TARGET_ROI_KEY', 'left_hipp')
    
    if roi_key not in mask_info:
        raise FileNotFoundError(f"ROI key '{roi_key}' not found in {mask_json_path}. Available: {list(mask_info.keys())}")
    
    mask_path = mask_info[roi_key]
    
    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"Mask file not found at: {mask_path}")
    
    img = nib.load(mask_path)
    mask_data = img.get_fdata()
    affine = img.affine
    
    return mask_data, affine

def find_functional_runs(subject_dir: Path) -> List[Path]:
    """
    Find all functional NIfTI files matching the pattern:
    sub-*/func/*task-narratives*.nii.gz
    """
    func_dir = subject_dir / "func"
    if not func_dir.exists():
        return []
    
    # Pattern from task description
    pattern = "*task-narratives*.nii.gz"
    runs = list(func_dir.glob(pattern))
    
    # Also try .nii if gzipped version not found (fallback)
    if not runs:
        pattern_uncompressed = "*task-narratives*.nii"
        runs = list(func_dir.glob(pattern_uncompressed))
    
    return sorted(runs)

def extract_roi_timecourse(nifti_path: Path, mask_data: np.ndarray, mask_affine: np.ndarray) -> Optional[np.ndarray]:
    """
    Load a NIfTI file, resample mask to data space if necessary, apply mask,
    and average voxels across the ROI for each timepoint.
    Returns a 1D array of shape (timepoints,).
    """
    try:
        func_img = nib.load(str(nifti_path))
        func_data = func_img.get_fdata()
        func_affine = func_img.affine
        
        # Check if data is 4D (x, y, z, t)
        if func_data.ndim != 4:
            logger.warning(f"Skipping {nifti_path}: Expected 4D data, got {func_data.ndim}D")
            return None
        
        # Resample mask to functional space if affine mismatch
        # Simple approach: use nilearn's resample_img if available, otherwise assume aligned
        # For robustness without heavy dependencies, we check affine similarity
        if not np.allclose(func_affine, mask_affine, atol=1e-3):
            # If not aligned, we must resample. Since nilearn is in requirements, use it.
            try:
                from nilearn.image import resample_to_img
                mask_img = nib.Nifti1Image(mask_data, mask_affine)
                resampled_mask = resample_to_img(mask_img, func_img, interpolation='nearest')
                mask_data = resampled_mask.get_fdata()
            except ImportError:
                logger.error("E001: nilearn not installed but mask resampling required. Cannot proceed.")
                raise RuntimeError("E001: nilearn required for mask resampling")
            except Exception as e:
                logger.error(f"E001: Failed to resample mask: {e}")
                raise
        
        # Apply mask: average non-zero voxels for each timepoint
        # mask_data is (x, y, z), func_data is (x, y, z, t)
        mask_indices = np.where(mask_data > 0)
        if len(mask_indices[0]) == 0:
            logger.warning(f"No valid voxels in mask for {nifti_path}")
            return None
        
        # Extract timecourses for all masked voxels
        # Shape: (n_voxels, n_timepoints)
        voxel_timecourses = func_data[mask_indices]
        
        # Average across voxels
        mean_timecourse = np.mean(voxel_timecourses, axis=0)
        
        return mean_timecourse
        
    except Exception as e:
        logger.error(f"E001: Failed to process {nifti_path}: {e}")
        raise

def process_subject(subject_dir: Path, mask_data: np.ndarray, mask_affine: np.ndarray, subject_id: str) -> Optional[np.ndarray]:
    """
    Process all functional runs for a subject and concatenate timecourses.
    Returns a 1D array of all timepoints, or None if no valid data found.
    """
    runs = find_functional_runs(subject_dir)
    if not runs:
        logger.warning(f"No functional runs found for {subject_id}")
        return None
    
    all_timecourses = []
    for run_path in runs:
        tc = extract_roi_timecourse(run_path, mask_data, mask_affine)
        if tc is not None:
            all_timecourses.append(tc)
    
    if not all_timecourses:
        return None
    
    # Concatenate timecourses from all runs
    return np.concatenate(all_timecourses)

def main():
    """
    Main entry point for T014: Extract Left Hippocampus timecourses.
    """
    # Configuration
    raw_data_dir = Path("data/raw/openneuro_ds001495")
    mask_json_path = "data/processed/mask_paths.json"
    output_path = Path("data/processed/roi_left_hipp.npy")
    
    # Check prerequisites
    if not raw_data_dir.exists():
        logger.error("E001: Raw data directory missing. Run T012 first.")
        sys.exit(1)
    
    if not mask_json_path.exists():
        logger.error("E001: Mask paths JSON missing. Run T013 first.")
        sys.exit(1)
    
    # Set environment for specific ROI
    os.environ['TARGET_ROI_KEY'] = 'left_hipp'
    
    try:
        mask_data, mask_affine = load_mask_from_json(mask_json_path)
    except FileNotFoundError as e:
        logger.error(f"E001: {e}")
        sys.exit(1)
    
    # Find subjects
    subjects = sorted([d for d in raw_data_dir.iterdir() if d.is_dir() and d.name.startswith('sub-')])
    
    if not subjects:
        logger.error("E001: No subjects found in raw data directory.")
        sys.exit(1)
    
    # Process first 10 subjects (or all if <10)
    target_subjects = subjects[:10]
    info(f"Processing {len(target_subjects)} subjects: {[s.name for s in target_subjects]}")
    
    all_subject_data = {}
    total_empty = 0
    
    for subj_dir in target_subjects:
        subj_id = subj_dir.name
        try:
            tc = process_subject(subj_dir, mask_data, mask_affine, subj_id)
            if tc is not None:
                if len(tc) == 0:
                    total_empty += 1
                    continue
                all_subject_data[subj_id] = tc
                info(f"  {subj_id}: {len(tc)} timepoints")
            else:
                total_empty += 1
        except Exception as e:
            logger.error(f"E001: Failed processing {subj_id}: {e}")
            # Continue with other subjects, but log error
    
    if len(all_subject_data) == 0:
        logger.error("E002: No valid timecourses extracted. All subjects failed or returned empty data.")
        sys.exit(2)
    
    # Determine max length for stacking (pad shorter ones with NaN if necessary)
    # Or store as object array if lengths vary significantly
    max_len = max(len(tc) for tc in all_subject_data.values())
    
    # Create output array: (n_subjects, max_timepoints)
    # Using float32 to save space, NaN for padding
    output_array = np.full((len(all_subject_data), max_len), np.nan, dtype=np.float32)
    subject_ids = sorted(all_subject_data.keys())
    
    for i, subj_id in enumerate(subject_ids):
        tc = all_subject_data[subj_id]
        output_array[i, :len(tc)] = tc.astype(np.float32)
    
    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, output_array)
    
    # Verify output
    loaded = np.load(output_path)
    info(f"Saved {output_path}: shape={loaded.shape}, dtype={loaded.dtype}")
    
    # Compute checksum
    checksum = compute_sha256(output_path)
    info(f"Checksum: {checksum}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
