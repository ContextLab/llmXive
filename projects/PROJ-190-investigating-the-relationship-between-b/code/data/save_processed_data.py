"""
Task T015: Save preprocessed time series to data/processed/ with checksums.

This module takes the preprocessed fMRI time series data (produced by 
code/data/preprocess.py), saves it to disk in a structured format, computes
SHA-256 checksums, and records these checksums in the project state YAML file.
"""
import os
import sys
import json
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import nibabel as nib

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import ensure_directories, validate_config, PROJECT_STATE_PATH
from code.utils.logging import get_logger, info, warning, error, debug
from code.utils.checksum import compute_file_sha256, save_checksums
from code.data.preprocess import main as run_preprocessing

logger = get_logger(__name__)

def save_time_series_nifti(
    subject_id: str,
    time_series: np.ndarray,
    reference_nifti: Path,
    output_dir: Path
) -> Path:
    """
    Save 2D time series (timepoints x regions) as a NIfTI file.
    
    We reconstruct a 4D NIfTI by reshaping the time series into (1, 1, regions, timepoints)
    or similar, but standard practice for ROI time series is often a 3D volume where
    each "voxel" represents a region, or a 4D file with singleton dimensions.
    
    For compatibility with neuroimaging tools, we will create a 4D NIfTI with shape
    (1, 1, num_regions, num_timepoints) and assign the affine from the reference.
    """
    if not reference_nifti.exists():
        raise FileNotFoundError(f"Reference NIfTI not found: {reference_nifti}")
    
    # Load reference to get affine and header
    ref_img = nib.load(str(reference_nifti))
    affine = ref_img.affine
    header = ref_img.header
    
    num_regions, num_timepoints = time_series.shape
    
    # Reshape to (1, 1, num_regions, num_timepoints) for 4D NIfTI
    # Note: This is a simplified representation. In real pipelines, 
    # one might map regions back to voxel space, but for ROI time series
    # this compact 4D format is often used.
    data_4d = time_series.T.reshape(1, 1, num_regions, num_timepoints)
    
    # Create NIfTI image
    img = nib.Nifti1Image(data_4d.astype(np.float32), affine, header)
    
    output_path = output_dir / f"{subject_id}_timeseries.nii.gz"
    nib.save(img, str(output_path))
    
    logger.info(f"Saved time series for {subject_id} to {output_path}")
    return output_path

def save_metadata(
    subject_id: str,
    metadata: Dict[str, Any],
    output_dir: Path
) -> Path:
    """Save subject-specific metadata as JSON."""
    output_path = output_dir / f"{subject_id}_metadata.json"
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata for {subject_id} to {output_path}")
    return output_path

def update_state_checksums(
    checksums: Dict[str, str],
    state_path: Optional[Path] = None
) -> None:
    """
    Update the project state YAML file with new artifact checksums.
    
    Args:
        checksums: Dictionary of {relative_path: sha256_hash}
        state_path: Path to the state YAML file (defaults to config)
    """
    if state_path is None:
        state_path = PROJECT_STATE_PATH
    
    # Ensure state directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create new
    if state_path.exists():
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {
            "project_id": "PROJ-190-investigating-the-relationship-between-b",
            "artifact_hashes": {}
        }
    
    # Update artifact_hashes
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    for path, checksum in checksums.items():
        state["artifact_hashes"][path] = checksum
    
    # Write back
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated state file at {state_path} with {len(checksums)} checksums")

def main():
    """
    Main entry point for T015.
    
    1. Run preprocessing (or load preprocessed data if already done)
    2. Save time series and metadata to data/processed/
    3. Compute SHA-256 checksums
    4. Update state YAML with checksums
    """
    # Ensure directories exist
    ensure_directories()
    
    # Get paths from config
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Run preprocessing to generate data (if not already done)
    # This will load, preprocess, and return the processed data
    logger.info("Starting preprocessing pipeline...")
    
    try:
        # Run the preprocessing main function which returns processed data
        # We assume preprocess.py main() handles loading and preprocessing
        # and saves intermediate results or returns data structures
        processed_data = run_preprocessing()
        
        if processed_data is None:
            error("Preprocessing returned no data. Check T013 implementation.")
            return 1
        
    except Exception as e:
        error(f"Preprocessing failed: {e}")
        return 1
    
    checksums = {}
    
    # Save each subject's data
    for subject_id, data in processed_data.items():
        try:
            time_series = data['time_series']  # (timepoints, regions)
            metadata = data['metadata']
            reference_path = data.get('reference_path')
            
            # Save time series as NIfTI
            if reference_path and Path(reference_path).exists():
                ts_path = save_time_series_nifti(
                    subject_id, 
                    time_series, 
                    Path(reference_path), 
                    processed_dir
                )
                rel_path = str(ts_path.relative_to(PROJECT_ROOT))
                checksum = compute_file_sha256(ts_path)
                checksums[rel_path] = checksum
            
            # Save metadata
            meta_path = save_metadata(subject_id, metadata, processed_dir)
            rel_path_meta = str(meta_path.relative_to(PROJECT_ROOT))
            checksum_meta = compute_file_sha256(meta_path)
            checksums[rel_path_meta] = checksum_meta
            
            info(f"Successfully saved and checksummed data for {subject_id}")
            
        except Exception as e:
            error(f"Failed to save data for {subject_id}: {e}")
            continue
    
    if not checksums:
        error("No checksums generated. Check if data was saved.")
        return 1
    
    # Update state file with checksums
    update_state_checksums(checksums)
    
    info(f"T015 complete. Saved {len(checksums) // 2} subjects with checksums.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
