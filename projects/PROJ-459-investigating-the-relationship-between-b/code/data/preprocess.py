"""
fMRIPrep preprocessing wrapper and time series extraction.

Runs fMRIPrep via Docker with memory limits and specific output configurations.
Extracts regional time courses using the Schaefer atlas.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd
import nibabel as nib

# Import from existing project modules
from config import get_data_path, get_processed_path, ensure_dirs
from utils.docker import validate_docker_daemon, check_fmriprep_image, pull_fmriprep_image
from utils.env_config import check_memory_limit, set_runtime_cap
from utils.io import ensure_dir
from utils.atlas import load_atlas, map_to_yeo, get_roi_networks
from data.models import TimeSeries

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# fMRIPrep configuration
FMRIPREP_VERSION = "23.1.3"
OUTPUT_SPACE = "MNI152NLin2009cAsym"
REQUIRED_CONFOUNDS = [
    "trans_x", "trans_y", "trans_z",
    "rot_x", "rot_y", "rot_z",
    "framewise_displacement", "dvars"
]

def run_fmriprep(subject_id: str, dataset_id: str = "ds000208", bids_dir: Optional[str] = None) -> bool:
    """
    Run fMRIPrep preprocessing for a specific subject via Docker.

    Args:
        subject_id: The subject identifier (e.g., 'sub-01')
        dataset_id: The OpenNeuro dataset ID (default: ds000208)
        bids_dir: Optional override for BIDS directory path

    Returns:
        True if preprocessing completed successfully, False otherwise.
    """
    # Validate environment
    logger.info(f"Validating Docker environment for subject {subject_id}...")
    if not validate_docker_daemon():
        logger.error("Docker daemon is not running. Cannot proceed with fMRIPrep.")
        return False

    if not check_fmriprep_image(FMRIPREP_VERSION):
        logger.info(f"fMRIPrep image {FMRIPREP_VERSION} not found. Attempting to pull...")
        if not pull_fmriprep_image(FMRIPREP_VERSION):
            logger.error("Failed to pull fMRIPrep image.")
            return False

    # Check memory limits
    check_memory_limit()

    # Set runtime cap if configured
    set_runtime_cap()

    # Determine paths
    if bids_dir is None:
        bids_dir = str(get_data_path(dataset_id))
    
    bids_path = Path(bids_dir)
    if not bids_path.exists():
        logger.error(f"BIDS directory does not exist: {bids_path}")
        return False

    # Create output directory
    output_dir = get_processed_path("fmriprep")
    ensure_dirs([output_dir])
    output_path = Path(output_dir)

    # Construct confounds string
    confounds_str = ",".join(REQUIRED_CONFOUNDS)

    # Build fMRIPrep command
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{bids_path}:/data:ro",
        "-v", f"{output_path}:/out",
        "-v", "/tmp/fmriprep_work:/work",
        "--name", f"fmriprep_{subject_id}",
        f"nipreps/fmriprep:{FMRIPREP_VERSION}",
        "/data", "/out", "participant",
        "--participant-label", subject_id,
        "--output-space", OUTPUT_SPACE,
        "--confounds", confounds_str,
        "--fs-no-reconall",
        "--skip-bids-validation",
        "-w", "/work"
    ]

    logger.info(f"Running fMRIPrep for {subject_id}...")
    logger.info(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600
        )

        if result.returncode != 0:
            logger.error(f"fMRIPrep failed for {subject_id}.")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False

        logger.info(f"fMRIPrep completed successfully for {subject_id}.")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"fMRIPrep timed out for {subject_id}.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running fMRIPrep for {subject_id}: {e}")
        return False

def extract_time_series(subject_id: str, dataset_id: str = "ds000208") -> Optional[Dict[str, np.ndarray]]:
    """
    Extract regional time courses using the Schaefer-400 atlas.
    
    This function loads the preprocessed BOLD data from fMRIPrep output,
    applies the Schaefer atlas mask, and computes the mean time series
    for each of the 400 ROIs.
    
    Args:
        subject_id: The subject identifier (e.g., 'sub-01')
        dataset_id: The OpenNeuro dataset ID (default: ds000208)
        
    Returns:
        Dict[str, np.ndarray]: Dictionary mapping ROI IDs to their time series (1D arrays).
        Returns None if extraction fails.
    """
    # Determine paths
    processed_dir = get_processed_path("fmriprep")
    bids_dir = get_data_path(dataset_id)
    
    # Construct path to the preprocessed BOLD file
    # fMRIPrep output structure: <subject>/func/sub-<subject>_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
    bold_path = Path(processed_dir) / subject_id / "func" / f"{subject_id}_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    
    if not bold_path.exists():
        logger.error(f"Preprocessed BOLD file not found for {subject_id}: {bold_path}")
        # Check if it's in a different structure (e.g., directly in subject folder)
        alt_bold_path = Path(processed_dir) / f"{subject_id}_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
        if alt_bold_path.exists():
            bold_path = alt_bold_path
        else:
            logger.error(f"Alternative BOLD path also not found: {alt_bold_path}")
            return None

    # Load the BOLD data
    try:
        bold_img = nib.load(str(bold_path))
        bold_data = bold_img.get_fdata()
        logger.info(f"Loaded BOLD data for {subject_id}: shape {bold_data.shape}")
    except Exception as e:
        logger.error(f"Failed to load BOLD data for {subject_id}: {e}")
        return None

    # Load the atlas
    try:
        atlas_df = load_atlas()
        atlas_df = map_to_yeo(atlas_df)
        roi_networks = get_roi_networks()
        logger.info(f"Loaded atlas with {len(atlas_df)} ROIs")
    except Exception as e:
        logger.error(f"Failed to load atlas: {e}")
        return None

    # The atlas file typically contains the label for each voxel.
    # We need to map the voxel labels to the ROIs.
    # However, the Schaefer atlas is usually provided as a NIfTI file where each voxel has a label.
    # We assume the atlas NIfTI file is available or can be constructed from the text file.
    # For this implementation, we will assume the text file provides the mapping and we need to
    # load the corresponding NIfTI atlas if available, or use a pre-registered atlas.
    # Since the text file alone doesn't give us the 3D mask, we will look for the NIfTI version.
    atlas_nifti_path = Path("data/raw/Schaefer2018_400Parcels_7Networks_order_FSLMNI152_2mm.nii.gz")
    if not atlas_nifti_path.exists():
        # Try to download or use a local copy
        logger.warning(f"Atlas NIfTI not found at {atlas_nifti_path}. Attempting to download...")
        # In a real scenario, we would download it here. For now, we assume it's in data/raw/
        logger.error("Atlas NIfTI file not found. Cannot extract time series.")
        return None

    try:
        atlas_img = nib.load(str(atlas_nifti_path))
        atlas_data = atlas_img.get_fdata()
        logger.info(f"Loaded atlas data: shape {atlas_data.shape}")
    except Exception as e:
        logger.error(f"Failed to load atlas NIfTI: {e}")
        return None

    # Ensure the atlas and BOLD data are in the same space
    # We assume they are both in MNI152NLin2009cAsym space as per fMRIPrep output
    
    # Extract time series for each ROI
    time_series_dict = {}
    unique_labels = np.unique(atlas_data)
    # Filter out background (label 0)
    roi_labels = [int(label) for label in unique_labels if label > 0]
    
    logger.info(f"Found {len(roi_labels)} ROIs in atlas")

    for label in roi_labels:
        # Create a mask for the current ROI
        mask = (atlas_data == label)
        
        # Apply the mask to the BOLD data
        # We need to handle the case where the BOLD data might have a different shape
        # We assume the atlas and BOLD are aligned
        if mask.shape != bold_data.shape[:3]:
            logger.error(f"Shape mismatch between atlas ({mask.shape}) and BOLD ({bold_data.shape[:3]})")
            continue
        
        # Get the time series for the current ROI by averaging across voxels
        roi_voxels = bold_data[mask, :]
        if roi_voxels.shape[0] == 0:
            logger.warning(f"No voxels found for ROI {label}")
            continue
        
        mean_ts = np.mean(roi_voxels, axis=0)
        
        # Map the label to an ROI ID
        # The text file has rows corresponding to ROI indices (1-based)
        # We need to find the row where the network label matches, but the text file
        # actually lists the network for each ROI index.
        # Let's assume the label in the NIfTI corresponds to the row index in the text file.
        # The text file has 400 rows, so label 1 -> row 0, label 400 -> row 399.
        roi_idx = label - 1
        if 0 <= roi_idx < len(atlas_df):
            roi_id = atlas_df.iloc[roi_idx]['roi_id']
            time_series_dict[roi_id] = mean_ts
        else:
            logger.warning(f"ROI label {label} out of range, skipping")

    logger.info(f"Extracted time series for {len(time_series_dict)} ROIs for {subject_id}")
    return time_series_dict

def main():
    """
    CLI entry point for preprocessing and time series extraction.
    Expects subject_id and optional dataset_id as arguments.
    """
    if len(sys.argv) < 2:
        print("Usage: python code/data/preprocess.py <subject_id> [dataset_id]")
        print("Example: python code/data/preprocess.py sub-01 ds000208")
        sys.exit(1)

    subject_id = sys.argv[1]
    dataset_id = sys.argv[2] if len(sys.argv) > 2 else "ds000208"

    # Run fMRIPrep
    success = run_fmriprep(subject_id, dataset_id)
    if not success:
        logger.error("Preprocessing failed, cannot extract time series.")
        sys.exit(1)

    # Extract time series
    time_series = extract_time_series(subject_id, dataset_id)
    if time_series is None:
        logger.error("Time series extraction failed.")
        sys.exit(1)

    # Save the time series to a file
    output_dir = get_processed_path("time_series")
    ensure_dirs([output_dir])
    output_file = Path(output_dir) / f"{subject_id}_time_series.npy"
    
    try:
        np.save(output_file, time_series)
        logger.info(f"Saved time series to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save time series: {e}")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()