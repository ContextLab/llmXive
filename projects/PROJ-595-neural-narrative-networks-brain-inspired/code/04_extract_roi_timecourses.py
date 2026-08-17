"""
Extract BOLD timecourses for specific ROIs from OpenNeuro ds001495.

This module implements the extraction logic for Right Hippocampus (and other ROIs).
It loads masks from the processed directory, iterates through subject functional runs,
and computes mean BOLD signal timecourses.

Dependencies:
    - T013: mask_paths.json must exist in data/processed/
    - T012: data/raw/ must contain downloaded ds001495
"""
import os
import json
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from utils.logging_config import get_logger, info, error, warning
from config import get_config

logger = get_logger(__name__)
config = get_config()


def load_mask_from_json(mask_registry_path: Path) -> Dict[str, Path]:
    """
    Load the mask registry JSON to get paths to ROI masks.
    
    Args:
        mask_registry_path: Path to data/processed/mask_paths.json
        
    Returns:
        Dict mapping ROI name (e.g., 'right_hipp') to Path of mask file
    """
    if not mask_registry_path.exists():
        raise FileNotFoundError(f"Mask registry not found: {mask_registry_path}")
    
    with open(mask_registry_path, 'r') as f:
        registry = json.load(f)
    
    return registry


def extract_roi_timecourse(
    func_nifti_path: Path,
    mask_nifti_path: Path
) -> np.ndarray:
    """
    Extract the mean BOLD timecourse for a specific ROI from a functional run.
    
    Args:
        func_nifti_path: Path to 4D functional NIfTI file (x, y, z, time)
        mask_nifti_path: Path to 3D binary mask NIfTI file
        
    Returns:
        1D numpy array of mean BOLD signal over time
    """
    # Load functional data
    func_img = nib.load(func_nifti_path)
    func_data = func_img.get_fdata()
    
    # Load mask data
    mask_img = nib.load(mask_nifti_path)
    mask_data = mask_img.get_fdata()
    
    # Ensure mask is binary
    mask_binary = (mask_data > 0).astype(bool)
    
    # Validate dimensions match
    if func_data.shape[:3] != mask_binary.shape:
        raise ValueError(
            f"Dimension mismatch: func {func_data.shape[:3]} vs mask {mask_binary.shape}"
        )
    
    # Reshape to (time, voxels) for efficient masking
    n_timepoints = func_data.shape[3]
    n_voxels = np.prod(func_data.shape[:3])
    
    func_2d = func_data.reshape(n_voxels, n_timepoints).T  # (time, voxels)
    mask_flat = mask_binary.reshape(-1)
    
    # Select only voxels inside the ROI
    roi_voxels = func_2d[:, mask_flat]
    
    if roi_voxels.shape[1] == 0:
        warning(f"No voxels found in mask for {func_nifti_path}")
        return np.zeros(n_timepoints)
    
    # Compute mean signal across ROI voxels for each timepoint
    mean_signal = np.mean(roi_voxels, axis=1)
    
    return mean_signal


def find_functional_runs(subject_dir: Path) -> List[Path]:
    """
    Find all functional NIfTI files for a subject in the OpenNeuro ds001495 structure.
    
    Args:
        subject_dir: Path to subject directory (e.g., data/raw/ds001495/sub-001)
        
    Returns:
        List of paths to functional NIfTI files
    """
    func_files = []
    # Standard OpenNeuro structure: sub-XX/func/sub-XX_task-*.nii.gz
    func_dir = subject_dir / "func"
    
    if not func_dir.exists():
        warning(f"No functional directory found for {subject_dir}")
        return []
    
    # Find all .nii.gz files in func directory
    for f in func_dir.glob("*.nii.gz"):
        # Filter for task-based functional runs (exclude fieldmap, etc.)
        if "task" in f.name:
            func_files.append(f)
    
    # Sort for consistency
    return sorted(func_files)


def process_subject(
    subject_id: str,
    raw_base: Path,
    mask_registry: Dict[str, Path],
    roi_name: str,
    output_dir: Path
) -> Optional[Dict[str, Any]]:
    """
    Process a single subject: extract ROI timecourse and save.
    
    Args:
        subject_id: Subject identifier (e.g., 'sub-001')
        raw_base: Base path to raw data (data/raw/)
        mask_registry: Dict of ROI names to mask paths
        roi_name: Name of the ROI to extract (e.g., 'right_hipp')
        output_dir: Directory to save the output .npy file
        
    Returns:
        Dict with extraction stats, or None if failed
    """
    subject_dir = raw_base / subject_id
    if not subject_dir.exists():
        warning(f"Subject directory not found: {subject_dir}")
        return None
    
    # Get mask path for this ROI
    if roi_name not in mask_registry:
        error(f"ROI '{roi_name}' not found in mask registry. Available: {list(mask_registry.keys())}")
        return None
    
    mask_path = Path(mask_registry[roi_name])
    if not mask_path.exists():
        error(f"Mask file not found: {mask_path}")
        return None
    
    # Find functional runs
    func_runs = find_functional_runs(subject_dir)
    if not func_runs:
        warning(f"No functional runs found for {subject_id}")
        return None
    
    info(f"Processing {subject_id}: {len(func_runs)} functional runs, ROI={roi_name}")
    
    # Aggregate timecourses across runs (simple concatenation for now)
    all_timecourses = []
    
    for run_path in func_runs:
        try:
            tc = extract_roi_timecourse(run_path, mask_path)
            if tc.size > 0:
                all_timecourses.append(tc)
        except Exception as e:
            error(f"Failed to extract timecourse from {run_path}: {e}")
            continue
    
    if not all_timecourses:
        warning(f"No valid timecourses extracted for {subject_id} - {roi_name}")
        return None
    
    # Concatenate timecourses (assuming consistent TR)
    full_timecourse = np.concatenate(all_timecourses)
    
    # Save output
    output_path = output_dir / f"{subject_id}_{roi_name}.npy"
    np.save(output_path, full_timecourse)
    
    info(f"Saved {output_path} (shape: {full_timecourse.shape})")
    
    return {
        "subject_id": subject_id,
        "roi": roi_name,
        "n_timepoints": len(full_timecourse),
        "n_runs": len(func_runs),
        "output_path": str(output_path)
    }


def main():
    """
    Main entry point: Extract Right Hippocampus timecourses for all subjects.
    
    This implements T015: Extract BOLD timecourses for Right Hippocampus.
    """
    logger.info("Starting T015: Right Hippocampus Timecourse Extraction")
    
    # Paths
    raw_base = Path("data/raw")
    processed_dir = Path("data/processed")
    output_dir = processed_dir
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load mask registry
    mask_registry_path = processed_dir / "mask_paths.json"
    if not mask_registry_path.exists():
        error("Mask registry (mask_paths.json) not found. Run T013 first.")
        return 1
    
    mask_registry = load_mask_from_json(mask_registry_path)
    logger.info(f"Loaded mask registry: {list(mask_registry.keys())}")
    
    # Define target ROI
    roi_name = "right_hipp"
    if roi_name not in mask_registry:
        error(f"ROI '{roi_name}' not found in mask registry. "
              f"Available: {list(mask_registry.keys())}")
        return 1
    
    # Find all subjects in raw data
    subject_dirs = sorted([d for d in raw_base.glob("sub-*") if d.is_dir()])
    
    if not subject_dirs:
        error(f"No subject directories found in {raw_base}")
        return 1
    
    logger.info(f"Found {len(subject_dirs)} subjects to process")
    
    # Process each subject
    results = []
    for subject_dir in subject_dirs:
        subject_id = subject_dir.name
        try:
            result = process_subject(
                subject_id=subject_id,
                raw_base=raw_base,
                mask_registry=mask_registry,
                roi_name=roi_name,
                output_dir=output_dir
            )
            if result:
                results.append(result)
        except Exception as e:
            error(f"Unexpected error processing {subject_id}: {e}")
            continue
    
    # Summary
    logger.info(f"T015 Complete: Extracted {len(results)} Right Hippocampus timecourses")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Files saved: {[r['output_path'] for r in results]}")
    
    return 0


if __name__ == "__main__":
    exit(main())