"""
Combine extracted ROI timecourses from T014, T015, T016 into a single NumPy array structure.
Loads roi_left_hipp.npy, roi_right_hipp.npy, and roi_dlpfc.npy and concatenates them.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path to allow relative imports if needed, though we use absolute imports here
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, error, info, warning
from config import get_config

logger = get_logger(__name__)

def load_roi_timecourse(file_path: str, roi_name: str) -> np.ndarray:
    """
    Load a single ROI timecourse .npy file.
    
    Args:
        file_path: Path to the .npy file
        roi_name: Name of the ROI for logging
        
    Returns:
        numpy array of timecourses
        
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file is empty or invalid
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"E001: File missing: {file_path}")
        raise FileNotFoundError(f"File missing: {file_path}")
    
    try:
        data = np.load(file_path)
        if data.size == 0:
            logger.error(f"E002: Empty timecourse data in {file_path}")
            raise ValueError(f"Empty timecourse data in {file_path}")
        
        info(f"Loaded {roi_name}: shape={data.shape}, dtype={data.dtype}")
        return data
    except Exception as e:
        logger.error(f"E001: Failed to load {file_path}: {str(e)}")
        raise

def extract_subject_ids(roi_data: np.ndarray, subject_prefix: str = "sub") -> list:
    """
    Extract subject IDs from the shape or metadata of the ROI data.
    Assuming data shape is (n_subjects, n_timepoints, n_voxels) or (n_subjects, n_timepoints).
    Returns a list of subject identifiers.
    """
    if roi_data.ndim < 2:
        raise ValueError("ROI data must have at least 2 dimensions (subjects, timepoints)")
    
    n_subjects = roi_data.shape[0]
    return [f"{subject_prefix}-{str(i+1).zfill(2)}" for i in range(n_subjects)]

def combine_roi_timecourses() -> np.ndarray:
    """
    Load all three ROI timecourses and combine them into a single structured array.
    
    Returns:
        Combined numpy array with shape (n_subjects, n_rois, n_timepoints, n_voxels)
        or a flattened representation depending on input shapes.
    """
    config = get_config()
    processed_dir = project_root / "data" / "processed"
    
    # Define input files based on T014, T015, T016
    roi_files = {
        "left_hipp": processed_dir / "roi_left_hipp.npy",
        "right_hipp": processed_dir / "roi_right_hipp.npy",
        "dlpfc": processed_dir / "roi_dlpfc.npy"
    }
    
    # Load all ROIs
    rois = {}
    for roi_name, file_path in roi_files.items():
        rois[roi_name] = load_roi_timecourse(str(file_path), roi_name)
    
    # Verify all ROIs have the same number of subjects and timepoints
    base_shape = rois["left_hipp"].shape
    for roi_name, data in rois.items():
        if data.shape[:2] != base_shape[:2]:
            error(f"Mismatch in ROI shapes: {roi_name} has shape {data.shape} vs expected {base_shape}")
            raise ValueError(f"ROI shape mismatch: {roi_name}")
    
    n_subjects, n_timepoints = base_shape[:2]
    
    # Determine the third dimension (voxels/features) for each ROI
    # Handle cases where data might be 2D (subjects, timepoints) or 3D (subjects, timepoints, voxels)
    voxel_dims = []
    for roi_name in ["left_hipp", "right_hipp", "dlpfc"]:
        if rois[roi_name].ndim == 2:
            # Reshape to 3D with 1 voxel
            rois[roi_name] = np.expand_dims(rois[roi_name], axis=-1)
            voxel_dims.append(1)
        else:
            voxel_dims.append(rois[roi_name].shape[2])
    
    info(f"Voxel dimensions: left_hipp={voxel_dims[0]}, right_hipp={voxel_dims[1]}, dlpfc={voxel_dims[2]}")
    
    # Concatenate along the voxel dimension (axis=2)
    # Result shape: (n_subjects, n_timepoints, total_voxels)
    combined = np.concatenate([
        rois["left_hipp"],
        rois["right_hipp"],
        rois["dlpfc"]
    ], axis=2)
    
    info(f"Combined timecourses shape: {combined.shape}")
    info(f"Total voxels: {combined.shape[2]}")
    
    # Save the combined array for downstream tasks
    output_path = processed_dir / "roi_timecourses_combined.npy"
    np.save(output_path, combined)
    info(f"Saved combined timecourses to {output_path}")
    
    # Also create a metadata file describing the structure
    metadata = {
        "shape": list(combined.shape),
        "n_subjects": n_subjects,
        "n_timepoints": n_timepoints,
        "n_total_voxels": combined.shape[2],
        "roi_voxel_counts": {
            "left_hipp": voxel_dims[0],
            "right_hipp": voxel_dims[1],
            "dlpfc": voxel_dims[2]
        },
        "subject_ids": extract_subject_ids(combined),
        "roi_order": ["left_hipp", "right_hipp", "dlpfc"],
        "voxel_ranges": {
            "left_hipp": (0, voxel_dims[0]),
            "right_hipp": (voxel_dims[0], voxel_dims[0] + voxel_dims[1]),
            "dlpfc": (voxel_dims[0] + voxel_dims[1], combined.shape[2])
        }
    }
    
    metadata_path = processed_dir / "roi_timecourses_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    info(f"Saved metadata to {metadata_path}")
    
    return combined

def main():
    """Main entry point for combining ROI timecourses."""
    try:
        info("Starting combination of ROI timecourses (T017a)")
        combined_data = combine_roi_timecourses()
        info("T017a completed successfully")
        return 0
    except Exception as e:
        error(f"T017a failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())