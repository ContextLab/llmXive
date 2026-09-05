import os
import sys
import json
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import List, Optional, Dict, Any

# Import from local utils as per API surface
from utils.logging_config import get_logger, error, info, warning
from config import get_config

logger = get_logger(__name__)

def load_mask_from_json(mask_json_path: str) -> np.ndarray:
    """Load a mask from a JSON file containing coordinates or path."""
    if not os.path.exists(mask_json_path):
        raise FileNotFoundError(f"Mask JSON file not found: {mask_json_path}")
    
    with open(mask_json_path, 'r') as f:
        mask_info = json.load(f)
    
    if "path" in mask_info:
        mask_path = mask_info["path"]
        if not os.path.exists(mask_path):
            raise FileNotFoundError(f"Mask file referenced in JSON not found: {mask_path}")
        mask_img = nib.load(mask_path)
        return mask_img.get_fdata()
    elif "coordinates" in mask_info:
        # Fallback for coordinate-based masks if path is missing
        coords = np.array(mask_info["coordinates"])
        # This is a simplified fallback; in reality, we'd reconstruct the image
        # For now, assume the mask path was correctly recorded in T013
        raise ValueError("Coordinate-based mask loading not fully implemented; use path-based mask.")
    else:
        raise ValueError("Mask JSON must contain either 'path' or 'coordinates'.")

def find_functional_runs(raw_dir: str, subject_id: str) -> List[Path]:
    """Find all functional NIfTI files for a given subject."""
    subject_dir = Path(raw_dir) / subject_id / "func"
    if not subject_dir.exists():
        return []
    
    # Pattern: sub-*/func/*task-narratives*.nii.gz
    pattern = f"*task-narratives*.nii.gz"
    runs = list(subject_dir.glob(pattern))
    return sorted(runs)

def extract_roi_timecourse(nifti_path: Path, mask_data: np.ndarray) -> Optional[np.ndarray]:
    """Extract average BOLD timecourse for a ROI from a NIfTI file."""
    try:
        img = nib.load(str(nifti_path))
        data = img.get_fdata()
        
        # Check dimensions: (x, y, z, t)
        if data.ndim != 4:
            logger.warning(f"Unexpected dimensionality for {nifti_path}: {data.ndim}D. Expected 4D.")
            return None
        
        # Ensure mask matches spatial dimensions
        if mask_data.shape != data.shape[:3]:
            # Attempt to resize or warn. For robustness, we assume masks are generated
            # to match the space of the functional data or are standard space.
            # If mismatch, we cannot simply average.
            logger.error(f"Mask shape {mask_data.shape} does not match image spatial shape {data.shape[:3]}.")
            return None
        
        # Apply mask: average over voxels where mask > 0
        # Flatten spatial dimensions
        spatial_data = data.reshape(-1, data.shape[-1])
        mask_flat = mask_data.flatten()
        
        # Identify active voxels
        active_voxels = mask_flat > 0
        if not np.any(active_voxels):
            logger.warning(f"No active voxels in mask for {nifti_path}.")
            return None
        
        # Average signal across active voxels for each timepoint
        timecourse = np.mean(spatial_data[active_voxels, :], axis=0)
        return timecourse
    except Exception as e:
        logger.error(f"Failed to extract timecourse from {nifti_path}: {e}")
        return None

def process_subject(subject_dir: Path, mask_data: np.ndarray, roi_name: str) -> Dict[str, Any]:
    """Process a single subject: find runs, extract timecourses, combine."""
    runs = find_functional_runs(str(subject_dir.parent), subject_dir.name)
    if not runs:
        logger.warning(f"No functional runs found for subject {subject_dir.name}.")
        return {"subject_id": subject_dir.name, "roi": roi_name, "timecourse": None}
    
    all_timecourses = []
    for run in runs:
        tc = extract_roi_timecourse(run, mask_data)
        if tc is not None:
            all_timecourses.append(tc)
    
    if not all_timecourses:
        logger.warning(f"No valid timecourses extracted for subject {subject_dir.name}.")
        return {"subject_id": subject_dir.name, "roi": roi_name, "timecourse": None}
    
    # Concatenate timecourses from multiple runs
    combined_tc = np.concatenate(all_timecourses, axis=0)
    return {"subject_id": subject_dir.name, "roi": roi_name, "timecourse": combined_tc}

def main():
    """Main entry point for DLPFC timecourse extraction."""
    config = get_config()
    raw_data_dir = Path("data/raw/openneuro_ds001495")
    mask_json_path = "data/processed/mask_paths.json"
    output_path = Path("data/processed/roi_dlpfc.npy")
    
    # Check prerequisites
    if not raw_data_dir.exists():
        error("E001", f"Raw data directory not found: {raw_data_dir}")
        sys.exit(1)
    
    if not os.path.exists(mask_json_path):
        error("E001", f"Mask paths JSON not found: {mask_json_path}")
        sys.exit(1)
    
    # Load DLPFC mask path
    with open(mask_json_path, 'r') as f:
        mask_paths = json.load(f)
    
    if "dlpfc" not in mask_paths:
        error("E001", "DLPFC mask path not found in mask_paths.json")
        sys.exit(1)
    
    dlpfc_mask_path = mask_paths["dlpfc"]
    if not os.path.exists(dlpfc_mask_path):
        error("E001", f"DLPFC mask file not found: {dlpfc_mask_path}")
        sys.exit(1)
    
    # Load mask data
    try:
        mask_img = nib.load(dlpfc_mask_path)
        mask_data = mask_img.get_fdata()
    except Exception as e:
        error("E001", f"Failed to load DLPFC mask: {e}")
        sys.exit(1)
    
    # Find subjects
    subjects = sorted([d for d in raw_data_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")])
    if not subjects:
        error("E001", f"No subjects found in {raw_data_dir}")
        sys.exit(1)
    
    # Process first 10 subjects
    subjects_to_process = subjects[:10]
    info(f"Processing {len(subjects_to_process)} subjects for DLPFC...")
    
    results = []
    for subj_dir in subjects_to_process:
        result = process_subject(subj_dir, mask_data, "dlpfc")
        if result["timecourse"] is not None:
            results.append(result)
        else:
            info(f"Skipping subject {subj_dir.name} due to extraction failure.")
    
    if not results:
        error("E002", "No valid timecourses extracted for any subject.")
        sys.exit(1)
    
    # Save results
    # Structure: list of (subject_id, timecourse_array)
    # We save as a structured array or a list of dicts converted to numpy
    # For simplicity and compatibility with T017a, we save a list of objects or a 2D array if aligned
    # Since timecourses may have different lengths, we save as a list of (id, tc)
    output_data = [
        {"subject_id": r["subject_id"], "timecourse": r["timecourse"].astype(np.float32)}
        for r in results
    ]
    
    try:
        np.save(output_path, output_data, allow_pickle=True)
        info(f"Successfully saved DLPFC timecourses to {output_path}")
    except Exception as e:
        error("E002", f"Failed to save output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()