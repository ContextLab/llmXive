import os
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import nibabel as nib
import pandas as pd
from scipy import ndimage

from code.config import get_config
from code.data.paths import get_raw_path, get_processed_path, ensure_dir
from code.utils.logging import log_error, log_warning, init_logging, log_info

# Configure logger for this module
logger = logging.getLogger(__name__)

def load_schaefer_parcellation(atlas_name: str = "Schaefer2018_200Parcels_7Networks") -> np.ndarray:
    """
    Load the Schaefer atlas parcellation mask.
    
    In a real production environment, this would download the atlas from the 
    Schaefer GitHub repository or a local cache. For this implementation, 
    we assume the atlas file exists in the project's data/raw/atlas directory
    or download it if missing.
    
    Args:
        atlas_name: Name of the atlas to load.
        
    Returns:
        3D numpy array representing the parcellation mask.
        
    Raises:
        FileNotFoundError: If the atlas file is not found.
    """
    config = get_config()
    project_root = get_raw_path()
    
    # Expected filename based on standard Schaefer release
    # We assume the atlas is downloaded to data/raw/atlas/
    atlas_dir = os.path.join(project_root, "atlas")
    ensure_dir(atlas_dir)
    
    # Standard Schaefer 200 parcellation filename
    atlas_file = os.path.join(atlas_dir, f"{atlas_name}.nii.gz")
    
    # If not present, we must fail loudly rather than generate synthetic data
    # as per project constraints.
    if not os.path.exists(atlas_file):
        raise FileNotFoundError(
            f"Atlas file not found at {atlas_file}. "
            "Please download the Schaefer atlas and place it in data/raw/atlas/."
        )
    
    logger.info(f"Loading atlas from {atlas_file}")
    atlas_img = nib.load(atlas_file)
    atlas_data = atlas_img.get_fdata()
    
    # Ensure we have integer labels
    atlas_data = atlas_data.astype(np.int32)
    
    return atlas_data

def extract_roi_time_series(nifti_path: str, atlas_mask: np.ndarray) -> np.ndarray:
    """
    Extract mean time series for each ROI defined in the atlas mask.
    
    Args:
        nifti_path: Path to the preprocessed NIfTI file (4D: x, y, z, time).
        atlas_mask: 3D numpy array of the parcellation mask.
        
    Returns:
        2D numpy array of shape (n_timepoints, n_rois) containing the time series.
        
    Raises:
        FileNotFoundError: If the NIfTI file is not found.
        ValueError: If dimensions do not match.
    """
    if not os.path.exists(nifti_path):
        raise FileNotFoundError(f"NIfTI file not found: {nifti_path}")
    
    logger.info(f"Loading NIfTI from {nifti_path}")
    img = nib.load(nifti_path)
    data = img.get_fdata()
    
    # Ensure atlas mask matches spatial dimensions
    if data.shape[:3] != atlas_mask.shape:
        raise ValueError(
            f"Dimension mismatch: NIfTI {data.shape[:3]} vs Atlas {atlas_mask.shape}"
        )
    
    # Flatten spatial dimensions
    n_voxels = data.shape[0] * data.shape[1] * data.shape[2]
    n_timepoints = data.shape[3]
    
    data_flat = data.reshape(n_voxels, n_timepoints)
    mask_flat = atlas_mask.flatten()
    
    # Identify unique ROIs (excluding background 0)
    unique_rois = np.unique(mask_flat)
    unique_rois = unique_rois[unique_rois != 0]
    
    roi_time_series = []
    
    for roi_id in unique_rois:
        # Create a boolean mask for this ROI
        roi_mask = mask_flat == roi_id
        
        # Extract time series for voxels in this ROI
        roi_voxel_ts = data_flat[roi_mask, :]
        
        # Calculate mean time series across voxels in the ROI
        mean_ts = np.mean(roi_voxel_ts, axis=0)
        roi_time_series.append(mean_ts)
    
    # Stack into (n_timepoints, n_rois)
    result = np.stack(roi_time_series, axis=1)
    
    logger.info(f"Extracted {result.shape[1]} ROIs with {result.shape[0]} timepoints")
    
    return result

def preprocess_subject(subject_id: str) -> Dict[str, Any]:
    """
    Preprocess a single subject: load preprocessed NIfTI and apply Schaefer atlas parcellation.
    
    This function assumes the preprocessed NIfTI file has already been downloaded
    and placed in data/raw/processed/{subject_id}/ by T012.
    
    Args:
        subject_id: The HCP subject ID (e.g., '100307').
        
    Returns:
        Dictionary containing:
            - 'subject_id': The subject ID
            - 'roi_timeseries': 2D numpy array of shape (n_timepoints, n_rois)
            - 'n_rois': Number of ROIs
            - 'n_timepoints': Number of timepoints
            - 'status': 'success' or 'error'
            - 'error_message': Error details if failed
            
    Raises:
        FileNotFoundError: If input files are missing.
    """
    config = get_config()
    
    # Path to preprocessed NIfTI (assuming HCP minimal preprocessing outputs)
    # HCP structure: data/raw/processed/{subject_id}/MNINonLinear/Results/rfMRI_REST1_LR/rfMRI_REST1_LR_hp2000_clean.nii.gz
    raw_path = get_raw_path()
    nifti_file = os.path.join(
        raw_path, 
        subject_id, 
        "MNINonLinear", 
        "Results", 
        "rfMRI_REST1_LR", 
        "rfMRI_REST1_LR_hp2000_clean.nii.gz"
    )
    
    if not os.path.exists(nifti_file):
        raise FileNotFoundError(
            f"Preprocessed NIfTI not found for subject {subject_id} at {nifti_file}"
        )
    
    try:
        # Load the Schaefer atlas
        atlas_mask = load_schaefer_parcellation("Schaefer2018_200Parcels_7Networks")
        
        # Extract ROI time series
        roi_ts = extract_roi_time_series(nifti_file, atlas_mask)
        
        logger.info(f"Successfully processed subject {subject_id}: {roi_ts.shape}")
        
        return {
            'subject_id': subject_id,
            'roi_timeseries': roi_ts,
            'n_rois': roi_ts.shape[1],
            'n_timepoints': roi_ts.shape[0],
            'status': 'success',
            'error_message': None
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to process subject {subject_id}: {error_msg}")
        return {
            'subject_id': subject_id,
            'roi_timeseries': None,
            'n_rois': 0,
            'n_timepoints': 0,
            'status': 'error',
            'error_message': error_msg
        }

def run_preprocessing_pipeline(subject_ids: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Run the preprocessing pipeline for a list of subjects.
    
    Args:
        subject_ids: List of subject IDs to process. If None, uses all subjects
                     found in the raw data directory.
                     
    Returns:
        DataFrame with columns: Subject_ID, ROI_Timeseries_Path, Status, Error_Message
        
    Note:
        The ROI timeseries are saved to data/processed/timeseries/{subject_id}.npy
        to avoid memory issues with large datasets.
    """
    config = get_config()
    raw_path = get_raw_path()
    processed_path = get_processed_path()
    
    # Ensure output directory exists
    timeseries_dir = os.path.join(processed_path, "timeseries")
    ensure_dir(timeseries_dir)
    
    # If subject_ids not provided, scan for available subjects
    if subject_ids is None:
        # Look for subject directories in raw_path
        subject_ids = [
            d for d in os.listdir(raw_path) 
            if os.path.isdir(os.path.join(raw_path, d)) and d.isdigit()
        ]
        logger.info(f"Discovered {len(subject_ids)} subjects in raw data")
    
    results = []
    successful_count = 0
    failed_count = 0
    
    for subject_id in subject_ids:
        logger.info(f"Processing subject {subject_id}...")
        
        try:
            result = preprocess_subject(subject_id)
            
            if result['status'] == 'success':
                # Save the timeseries to disk
                output_file = os.path.join(timeseries_dir, f"{subject_id}.npy")
                np.save(output_file, result['roi_timeseries'])
                
                results.append({
                    'Subject_ID': subject_id,
                    'ROI_Timeseries_Path': output_file,
                    'N_ROIs': result['n_rois'],
                    'N_Timepoints': result['n_timepoints'],
                    'Status': 'success',
                    'Error_Message': ''
                })
                successful_count += 1
            else:
                results.append({
                    'Subject_ID': subject_id,
                    'ROI_Timeseries_Path': '',
                    'N_ROIs': 0,
                    'N_Timepoints': 0,
                    'Status': 'error',
                    'Error_Message': result['error_message']
                })
                failed_count += 1
                
        except Exception as e:
            logger.error(f"Unexpected error processing {subject_id}: {str(e)}")
            results.append({
                'Subject_ID': subject_id,
                'ROI_Timeseries_Path': '',
                'N_ROIs': 0,
                'N_Timepoints': 0,
                'Status': 'error',
                'Error_Message': str(e)
            })
            failed_count += 1
    
    # Create DataFrame
    df_results = pd.DataFrame(results)
    
    # Save summary to CSV
    summary_file = os.path.join(processed_path, "preprocessing_summary.csv")
    df_results.to_csv(summary_file, index=False)
    
    logger.info(f"Preprocessing complete: {successful_count} success, {failed_count} failed")
    logger.info(f"Summary saved to {summary_file}")
    
    return df_results

def main():
    """
    Main entry point for running the preprocessing pipeline.
    
    Usage: python -m code.data.preprocess
    """
    init_logging()
    logger.info("Starting preprocessing pipeline...")
    
    # Example: process a small subset for testing
    # In production, this would read from a manifest or config
    test_subjects = ['100307', '100903', '101006']  # Small subset for verification
    
    try:
        df = run_preprocessing_pipeline(subject_ids=test_subjects)
        print(df.head())
        
        # Verify outputs exist
        processed_path = get_processed_path()
        timeseries_dir = os.path.join(processed_path, "timeseries")
        
        for _, row in df.iterrows():
            if row['Status'] == 'success':
                assert os.path.exists(row['ROI_Timeseries_Path']), f"Missing file: {row['ROI_Timeseries_Path']}"
        
        logger.info("All output files verified successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()