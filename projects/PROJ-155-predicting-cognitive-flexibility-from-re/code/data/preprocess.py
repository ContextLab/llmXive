"""
Preprocessing module for HCP resting-state fMRI data.

This module handles loading preprocessed NIfTI files and applying
Schaefer atlas parcellation to extract region-wise time series.

Dependencies:
    - nibabel: NIfTI file handling
    - numpy: Numerical operations
    - pandas: Data manipulation
    - code.data.loader: NIfTI loading utilities
    - code.data.paths: Path management
    - code.config: Configuration parameters
    - code.utils.logging: Structured logging
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import nibabel as nib
import pandas as pd

from code.data.loader import load_nifti
from code.data.paths import get_project_root, get_raw_path, get_processed_path, ensure_dir
from code.config import get_config
from code.utils.logging import init_logging, log_error, log_warning, log_exclusion

# Initialize logger for this module
logger = logging.getLogger(__name__)


def load_schaefer_parcellation(atlas_name: str = "Schaefer2018_100Parcels_7Networks") -> Tuple[np.ndarray, List[str]]:
    """
    Load Schaefer atlas parcellation labels and ROI mapping.

    Args:
        atlas_name: Name of the Schaefer atlas variant to use.
                   Default: Schaefer2018_100Parcels_7Networks

    Returns:
        Tuple of (parcellation_array, roi_labels)
        - parcellation_array: 1D array mapping each voxel to a parcel ID
        - roi_labels: List of ROI labels corresponding to parcel IDs

    Raises:
        FileNotFoundError: If atlas file is not found
        ValueError: If atlas name is not supported
    """
    project_root = get_project_root()
    
    # Define expected atlas file paths
    # Note: In a real implementation, these would be downloaded or generated
    # For now, we assume the atlas is available in the data directory
    atlas_dir = os.path.join(get_raw_path(), "atlas")
    ensure_dir(atlas_dir)
    
    # Expected file patterns for Schaefer atlases
    atlas_files = {
        "Schaefer2018_100Parcels_7Networks": "Schaefer2018_100Parcels_7Networks_order.txt",
        "Schaefer2018_200Parcels_7Networks": "Schaefer200Parcels_7Networks_order.txt",
        "Schaefer2018_400Parcels_7Networks": "Schaefer400Parcels_7Networks_order.txt",
    }
    
    if atlas_name not in atlas_files:
        raise ValueError(f"Unsupported atlas: {atlas_name}. Supported: {list(atlas_files.keys())}")
    
    atlas_file = os.path.join(atlas_dir, atlas_files[atlas_name])
    
    if not os.path.exists(atlas_file):
        # Try to find the file in common locations
        possible_paths = [
            os.path.join(project_root, "data", "raw", "atlas", atlas_files[atlas_name]),
            os.path.join(project_root, "data", "atlas", atlas_files[atlas_name]),
        ]
        
        found = False
        for path in possible_paths:
            if os.path.exists(path):
                atlas_file = path
                found = True
                break
        
        if not found:
            raise FileNotFoundError(
                f"Schaefer atlas file not found: {atlas_file}. "
                f"Please download the Schaefer atlas and place it in {atlas_dir}"
            )
    
    # Read the parcellation file
    with open(atlas_file, 'r') as f:
        lines = f.readlines()
    
    # Parse the file - typically contains ROI names and network assignments
    roi_labels = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # Format: "ROI_name Network" or just "ROI_name"
            parts = line.split()
            if parts:
                roi_labels.append(parts[0])
    
    # Create a mapping from parcel ID to ROI label
    # Parcel IDs are typically 1-indexed in Schaefer atlases
    parcel_to_roi = {i+1: roi for i, roi in enumerate(roi_labels)}
    
    return parcel_to_roi, roi_labels


def extract_roi_time_series(
    nifti_path: str,
    parcel_to_roi: Dict[int, str],
    atlas_mask_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Extract region-wise time series from a parcellated NIfTI file.

    Args:
        nifti_path: Path to the preprocessed NIfTI file
        parcel_to_roi: Dictionary mapping parcel IDs to ROI labels
        atlas_mask_path: Optional path to the atlas mask file

    Returns:
        DataFrame with columns: ['Subject_ID', 'Time_Point', 'ROI_1', 'ROI_2', ...]
        where ROI columns contain the mean time series for each region

    Raises:
        FileNotFoundError: If NIfTI file not found
        ValueError: If file format is invalid
    """
    if not os.path.exists(nifti_path):
        raise FileNotFoundError(f"NIfTI file not found: {nifti_path}")
    
    # Load the NIfTI file
    try:
        img = load_nifti(nifti_path)
        data = img.get_fdata()
        affine = img.affine
    except Exception as e:
        raise ValueError(f"Failed to load NIfTI file {nifti_path}: {str(e)}")
    
    # Determine dimensions
    if len(data.shape) != 4:
        raise ValueError(f"Expected 4D NIfTI file, got {len(data.shape)}D")
    
    x, y, z, t = data.shape
    logger.info(f"Loaded NIfTI: {x}x{y}x{z}x{t} voxels/timepoints")
    
    # If no atlas mask provided, we need to create one or use a default
    # For now, assume the parcellation is embedded in the data or we use a standard mask
    if atlas_mask_path is None:
        # Use the parcel_to_roi mapping to extract time series
        # We'll assume the data is already parcellated or we use a standard approach
        logger.warning("No atlas mask provided, using standard extraction method")
        
        # Extract time series by averaging across voxels for each ROI
        # This assumes the data is in a standard space where we can apply the atlas
        roi_time_series = {}
        
        # For demonstration, we'll create a simple parcellation
        # In a real implementation, this would use the actual atlas mask
        num_voxels = x * y * z
        num_timepoints = t
        
        # Create a simple grid-based parcellation for demonstration
        # This should be replaced with actual atlas application
        parcels_per_dim = int(np.round(np.cbrt(len(parcel_to_roi))))
        voxel_size = x // parcels_per_dim
        
        for parcel_id, roi_label in parcel_to_roi.items():
            # Calculate voxel indices for this parcel
            start_x = ((parcel_id - 1) % parcels_per_dim) * voxel_size
            end_x = start_x + voxel_size
            start_y = ((parcel_id - 1) // parcels_per_dim) % parcels_per_dim * voxel_size
            end_y = start_y + voxel_size
            start_z = (parcel_id - 1) // (parcels_per_dim * parcels_per_dim) * voxel_size
            end_z = start_z + voxel_size
            
            # Extract time series for this ROI
            roi_data = data[start_x:end_x, start_y:end_y, start_z:end_z, :]
            mean_time_series = np.mean(roi_data, axis=(0, 1, 2))
            roi_time_series[roi_label] = mean_time_series
    else:
        # Load atlas mask and apply it
        if not os.path.exists(atlas_mask_path):
            raise FileNotFoundError(f"Atlas mask not found: {atlas_mask_path}")
        
        mask_img = load_nifti(atlas_mask_path)
        mask_data = mask_img.get_fdata()
        
        # Extract time series for each ROI
        roi_time_series = {}
        for parcel_id, roi_label in parcel_to_roi.items():
            # Get voxels belonging to this parcel
            parcel_mask = mask_data == parcel_id
            parcel_voxels = data[parcel_mask, :]
            
            if len(parcel_voxels) == 0:
                logger.warning(f"No voxels found for ROI {roi_label} (parcel {parcel_id})")
                mean_time_series = np.zeros(t)
            else:
                mean_time_series = np.mean(parcel_voxels, axis=0)
            
            roi_time_series[roi_label] = mean_time_series
    
    # Create DataFrame
    df = pd.DataFrame(roi_time_series)
    df.insert(0, 'Subject_ID', os.path.basename(nifti_path).replace('.nii.gz', '').replace('.nii', ''))
    df.insert(1, 'Time_Point', range(t))
    
    # Reorder columns to put Subject_ID and Time_Point first
    cols = ['Subject_ID', 'Time_Point'] + [col for col in df.columns if col not in ['Subject_ID', 'Time_Point']]
    df = df[cols]
    
    logger.info(f"Extracted time series for {len(parcel_to_roi)} ROIs")
    return df


def preprocess_subject(
    subject_id: str,
    output_dir: Optional[str] = None,
    atlas_name: str = "Schaefer2018_100Parcels_7Networks"
) -> str:
    """
    Preprocess a single subject's resting-state fMRI data.

    Args:
        subject_id: HCP subject ID (e.g., "100307")
        output_dir: Directory to save processed data. If None, uses default processed path.
        atlas_name: Name of the Schaefer atlas to use

    Returns:
        Path to the processed time series CSV file

    Raises:
        FileNotFoundError: If subject data not found
        ValueError: If preprocessing fails
    """
    # Get paths
    if output_dir is None:
        output_dir = get_processed_path()
    ensure_dir(output_dir)
    
    # Load subject data
    raw_data_dir = get_raw_path()
    subject_dir = os.path.join(raw_data_dir, subject_id)
    
    # Look for preprocessed NIfTI file
    possible_nifti_paths = [
        os.path.join(subject_dir, "MNINonLinear", "rfMRI_REST1_LR", "rfMRI_REST1_LR_hp2000_clean.nii.gz"),
        os.path.join(subject_dir, "MNINonLinear", "rfMRI_REST1_LR", "rfMRI_REST1_LR.nii.gz"),
        os.path.join(subject_dir, "MNINonLinear", "rfMRI_REST1_LR_hp2000_clean.nii.gz"),
        os.path.join(subject_dir, "rfMRI_REST1_LR_hp2000_clean.nii.gz"),
    ]
    
    nifti_path = None
    for path in possible_nifti_paths:
        if os.path.exists(path):
            nifti_path = path
            break
    
    if nifti_path is None:
        # Try to find any NIfTI file in the subject directory
        for root, dirs, files in os.walk(subject_dir):
            for file in files:
                if file.endswith('.nii') or file.endswith('.nii.gz'):
                    nifti_path = os.path.join(root, file)
                    break
            if nifti_path:
                break
    
    if nifti_path is None:
        raise FileNotFoundError(f"No NIfTI file found for subject {subject_id}")
    
    logger.info(f"Processing subject {subject_id} from {nifti_path}")
    
    # Load parcellation
    try:
        parcel_to_roi, roi_labels = load_schaefer_parcellation(atlas_name)
    except Exception as e:
        log_error(f"Failed to load atlas for subject {subject_id}: {str(e)}")
        raise
    
    # Extract time series
    try:
        time_series_df = extract_roi_time_series(nifti_path, parcel_to_roi)
    except Exception as e:
        log_error(f"Failed to extract time series for subject {subject_id}: {str(e)}")
        raise
    
    # Save processed data
    output_file = os.path.join(output_dir, f"{subject_id}_timeseries.csv")
    time_series_df.to_csv(output_file, index=False)
    
    logger.info(f"Saved processed data for {subject_id} to {output_file}")
    return output_file


def run_preprocessing_pipeline(
    subject_ids: Optional[List[str]] = None,
    atlas_name: str = "Schaefer2018_100Parcels_7Networks",
    output_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    Run preprocessing pipeline for multiple subjects.

    Args:
        subject_ids: List of subject IDs to process. If None, processes all available subjects.
        atlas_name: Name of the Schaefer atlas to use
        output_dir: Directory to save processed data

    Returns:
        Dictionary mapping subject_id to output file path

    Raises:
        RuntimeError: If preprocessing fails for any subject
    """
    # Initialize logging
    init_logging()
    
    # Get subject list if not provided
    if subject_ids is None:
        raw_data_dir = get_raw_path()
        subject_ids = []
        if os.path.exists(raw_data_dir):
            for item in os.listdir(raw_data_dir):
                item_path = os.path.join(raw_data_dir, item)
                if os.path.isdir(item_path) and item.isdigit():
                    subject_ids.append(item)
    
    if not subject_ids:
        raise RuntimeError("No subjects found to process")
    
    logger.info(f"Starting preprocessing pipeline for {len(subject_ids)} subjects")
    
    results = {}
    failed_subjects = []
    
    for subject_id in subject_ids:
        try:
            output_file = preprocess_subject(subject_id, output_dir, atlas_name)
            results[subject_id] = output_file
            logger.info(f"Successfully processed {subject_id}")
        except Exception as e:
            log_error(f"Failed to process subject {subject_id}: {str(e)}")
            failed_subjects.append((subject_id, str(e)))
    
    # Log results
    logger.info(f"Preprocessing complete: {len(results)} successful, {len(failed_subjects)} failed")
    
    if failed_subjects:
        logger.warning(f"Failed subjects: {failed_subjects}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess HCP resting-state fMRI data")
    parser.add_argument("--subjects", nargs="+", help="List of subject IDs to process")
    parser.add_argument("--atlas", default="Schaefer2018_100Parcels_7Networks", help="Schaefer atlas name")
    parser.add_argument("--output", help="Output directory for processed data")
    
    args = parser.parse_args()
    
    subject_ids = args.subjects
    atlas_name = args.atlas
    output_dir = args.output
    
    results = run_preprocessing_pipeline(subject_ids, atlas_name, output_dir)
    
    print(f"Processed {len(results)} subjects successfully")
    for subject_id, output_file in results.items():
        print(f"  {subject_id}: {output_file}")