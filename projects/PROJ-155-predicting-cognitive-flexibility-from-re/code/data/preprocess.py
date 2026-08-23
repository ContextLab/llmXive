"""
Preprocessing module for rs-fMRI data.
Handles loading of preprocessed NIfTI files and application of Schaefer atlas parcellation.
"""
import os
import logging
import tarfile
import tempfile
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import nibabel as nib
import pandas as pd
from scipy import ndimage

from code.config import get_config
from code.data.paths import get_raw_path, get_processed_path, ensure_dir
from code.utils.logging import log_error, log_warning, init_logging

# Initialize logger
logger = logging.getLogger(__name__)

# Atlas configuration
ATLAS_URL = "https://schaefer2018.atlases.nitrc.org/Schaefer2018_200Parcels_7Networks_order_FSLMNI152.tar.gz"
ATLAS_FILENAME = "Schaefer2018_200Parcels_7Networks_order_FSLMNI152.nii.gz"
ATLAS_DIR_NAME = "Schaefer2018"

def _get_atlas_local_path() -> str:
    """Returns the local path where the atlas should be stored."""
    raw_path = get_raw_path()
    atlas_dir = os.path.join(raw_path, ATLAS_DIR_NAME)
    ensure_dir(atlas_dir)
    return os.path.join(atlas_dir, ATLAS_FILENAME)

def _download_atlas(atlas_url: str, local_path: str) -> str:
    """
    Downloads the Schaefer atlas if it doesn't exist.
    Handles .tar.gz extraction if necessary.
    """
    if os.path.exists(local_path):
        logger.info(f"Atlas already exists at {local_path}")
        return local_path

    import requests
    logger.info(f"Downloading atlas from {atlas_url}...")
    
    # Download to a temp file first
    temp_dir = tempfile.gettempdir()
    temp_tar = os.path.join(temp_dir, "schaefer_atlas.tar.gz")
    
    try:
        response = requests.get(atlas_url, stream=True, timeout=300)
        response.raise_for_status()
        
        with open(temp_tar, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Downloaded atlas to {temp_tar}, extracting...")
        
        # Extract
        with tarfile.open(temp_tar, 'r:gz') as tar:
            # The archive usually contains the nii.gz directly or in a subfolder
            # We look for the specific filename
            members = tar.getmembers()
            target_member = None
            for member in members:
                if ATLAS_FILENAME in member.name:
                    target_member = member
                    break
            
            if target_member:
                # Extract to the target directory
                target_file = os.path.join(os.path.dirname(local_path), target_member.name)
                tar.extract(target_member, path=os.path.dirname(local_path))
                
                # If the extracted file has a different path (e.g. in a subfolder), move it
                if not os.path.exists(local_path) and os.path.exists(target_file):
                    os.rename(target_file, local_path)
                elif os.path.exists(local_path):
                    pass # Already there
                else:
                    raise FileNotFoundError(f"Could not locate {ATLAS_FILENAME} after extraction")
            else:
                raise FileNotFoundError(f"Could not find {ATLAS_FILENAME} in the archive")
        
        os.remove(temp_tar)
        logger.info("Atlas extraction complete.")
        
    except requests.RequestException as e:
        log_error(f"Failed to download atlas: {e}")
        raise RuntimeError(f"Data Gap: Real atlas unavailable at {atlas_url}") from e
    except Exception as e:
        log_error(f"Failed to extract atlas: {e}")
        raise

    return local_path

def load_schaefer_parcellation(atlas_url: str = ATLAS_URL) -> nib.Nifti1Image:
    """
    Loads the Schaefer 200-parcel atlas. Downloads if necessary.
    
    Returns:
        nib.Nifti1Image: The atlas image object.
    """
    local_path = _get_atlas_local_path()
    _download_atlas(atlas_url, local_path)
    
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Atlas file not found at {local_path} after download attempt")
        
    atlas_img = nib.load(local_path)
    logger.info(f"Loaded Schaefer atlas: shape={atlas_img.shape}, dtype={atlas_img.get_data_dtype()}")
    return atlas_img

def extract_roi_time_series(
    subject_nifti_path: str,
    atlas_img: nib.Nifti1Image
) -> np.ndarray:
    """
    Extracts the mean time series for each ROI defined in the atlas.
    
    Args:
        subject_nifti_path: Path to the preprocessed NIfTI file (4D).
        atlas_img: The Schaefer atlas image (3D).
        
    Returns:
        np.ndarray: Array of shape (n_timepoints, n_rois).
    """
    # Load subject data
    subject_img = nib.load(subject_nifti_path)
    subject_data = subject_img.get_fdata()
    
    # Get atlas labels
    atlas_data = atlas_img.get_fdata()
    unique_labels = np.unique(atlas_data)
    # Filter out background (0)
    roi_labels = unique_labels[unique_labels > 0]
    n_rois = len(roi_labels)
    
    # Sort labels to ensure consistent ordering
    roi_labels = np.sort(roi_labels)
    
    # Check dimensions
    if subject_data.ndim != 4:
        raise ValueError(f"Subject data must be 4D, got {subject_data.ndim}D")
    
    if atlas_data.shape != subject_data.shape[:3]:
        # Attempt resampling if shapes mismatch (common in HCP vs atlas)
        logger.warning(f"Shape mismatch: Subject {subject_data.shape[:3]} vs Atlas {atlas_data.shape}. Resampling atlas to subject space.")
        # Use nearest neighbor interpolation to preserve integer labels
        atlas_data_resampled = ndimage.zoom(
            atlas_data, 
            np.array(subject_data.shape[:3]) / np.array(atlas_data.shape),
            order=0
        )
        # Ensure we still have integer labels after resampling
        atlas_data_resampled = np.round(atlas_data_resampled).astype(int)
        # Re-map labels to ensure they are contiguous if gaps were introduced by resampling
        # (Optional, but good for robustness. For now, we just use the values found).
        # Actually, simpler: just use the resampled data as the mask source.
        # We need to know which unique values exist in the resampled atlas.
        final_roi_labels = np.unique(atlas_data_resampled)
        final_roi_labels = final_roi_labels[final_roi_labels > 0]
    else:
        atlas_data_resampled = atlas_data
        final_roi_labels = roi_labels

    n_timepoints = subject_data.shape[3]
    time_series = np.zeros((n_timepoints, n_rois), dtype=np.float32)
    
    logger.info(f"Extracting time series for {n_rois} ROIs...")
    
    for i, label in enumerate(final_roi_labels):
        mask = (atlas_data_resampled == label)
        # Extract mean time series for this ROI
        # subject_data is (X, Y, Z, Time)
        roi_data = subject_data[mask]
        # Reshape to (n_voxels, n_timepoints) to take mean across voxels
        if roi_data.size == 0:
            logger.warning(f"ROI {label} has no voxels. Skipping.")
            continue
        
        # roi_data is 1D array of all voxels in this ROI across all timepoints?
        # No, subject_data[mask] flattens the first 3 dims.
        # We need to reshape carefully.
        # Better approach: iterate timepoints or use advanced indexing.
        # subject_data[mask, :] doesn't work directly if mask is 3D.
        # subject_data[mask] returns a 1D array of all selected voxels for all timepoints?
        # Actually, nibabel data is (X, Y, Z, T).
        # subject_data[mask] where mask is (X,Y,Z) returns (n_voxels, T) if we are careful?
        # Let's use the standard numpy boolean indexing:
        # data[mask] -> (n_voxels * T) ? No.
        # We need to reshape subject_data to (n_voxels, T) first?
        
        # Correct way for 4D data:
        # subject_data is (X, Y, Z, T)
        # We want mean over voxels for each timepoint.
        
        # Reshape to (N, T) where N = X*Y*Z
        n_voxels_total = subject_data.shape[0] * subject_data.shape[1] * subject_data.shape[2]
        subject_2d = subject_data.reshape(n_voxels_total, n_timepoints)
        
        # Create a flat mask
        flat_mask = mask.reshape(n_voxels_total)
        selected_voxels = subject_2d[flat_mask, :] # (n_roi_voxels, T)
        
        if selected_voxels.shape[0] > 0:
            mean_ts = np.mean(selected_voxels, axis=0)
            time_series[:, i] = mean_ts
        else:
            time_series[:, i] = np.nan
            
    return time_series

def preprocess_subject(
    subject_id: str,
    subject_nifti_path: str,
    atlas_img: Optional[nib.Nifti1Image] = None
) -> Tuple[str, np.ndarray]:
    """
    Preprocesses a single subject: loads NIfTI, extracts ROI time series.
    
    Args:
        subject_id: The subject identifier.
        subject_nifti_path: Path to the preprocessed NIfTI file.
        atlas_img: Optional pre-loaded atlas image.
        
    Returns:
        Tuple of (output_path, time_series_array)
    """
    if atlas_img is None:
        atlas_img = load_schaefer_parcellation()
    
    if not os.path.exists(subject_nifti_path):
        log_error(f"Subject NIfTI not found: {subject_nifti_path}")
        raise FileNotFoundError(f"Subject data missing: {subject_nifti_path}")
    
    try:
        time_series = extract_roi_time_series(subject_nifti_path, atlas_img)
    except Exception as e:
        log_error(f"Failed to extract time series for {subject_id}: {e}")
        raise
    
    # Save the processed time series as a CSV
    processed_dir = get_processed_path()
    ensure_dir(processed_dir)
    output_filename = f"{subject_id}_timeseries.csv"
    output_path = os.path.join(processed_dir, output_filename)
    
    # Create DataFrame
    df = pd.DataFrame(time_series)
    df.columns = [f"ROI_{i+1}" for i in range(df.shape[1])]
    df.insert(0, "Timepoint", range(df.shape[0]))
    df.insert(0, "Subject_ID", subject_id)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed time series for {subject_id} to {output_path}")
    
    return output_path, time_series

def run_preprocessing_pipeline(subject_ids: Optional[List[str]] = None) -> List[str]:
    """
    Runs the preprocessing pipeline for a list of subjects.
    If subject_ids is None, attempts to discover subjects from the raw data directory.
    
    Args:
        subject_ids: List of subject IDs to process.
        
    Returns:
        List of paths to processed CSV files.
    """
    init_logging()
    logger.info("Starting preprocessing pipeline...")
    
    if subject_ids is None:
        # Discover subjects from raw directory
        raw_path = get_raw_path()
        hcp_dir = os.path.join(raw_path, "HCP_1200")
        if os.path.exists(hcp_dir):
            subject_ids = [d for d in os.listdir(hcp_dir) if os.path.isdir(os.path.join(hcp_dir, d))]
        else:
            log_error(f"Raw data directory not found: {hcp_dir}")
            return []
    
    if not subject_ids:
        logger.warning("No subjects found to process.")
        return []
    
    atlas_img = load_schaefer_parcellation()
    processed_paths = []
    
    for sid in subject_ids:
        # Construct expected path to the preprocessed NIfTI from T012
        # T012 saves to data/raw/HCP_1200/{subject_id}/...
        # We need to find the specific NIfTI file. Usually "MNINonLinear/Results/rHCP...nii"
        # For this task, we assume a standard naming or look for the first valid 4D nifti
        raw_subj_dir = os.path.join(get_raw_path(), "HCP_1200", sid)
        if not os.path.exists(raw_subj_dir):
            log_warning(f"Subject directory not found: {raw_subj_dir}")
            continue
        
        # Find NIfTI file
        nifti_files = [f for f in os.listdir(raw_subj_dir) if f.endswith('.nii') or f.endswith('.nii.gz')]
        if not nifti_files:
            # Recursively search if needed, but usually it's in a subfolder like MNINonLinear/Results
            found = False
            for root, dirs, files in os.walk(raw_subj_dir):
                for f in files:
                    if f.endswith('.nii') or f.endswith('.nii.gz'):
                        # Skip non-resting state if possible (heuristic: contains 'r' or 'func')
                        if 'r' in f.lower() or 'func' in f.lower():
                            nifti_files = [os.path.join(root, f)]
                            found = True
                            break
                if found: break
        
        if not nifti_files:
            log_error(f"No NIfTI file found for subject {sid}")
            continue
            
        # Assume the first valid one is the resting state
        nifti_path = os.path.join(raw_subj_dir, nifti_files[0])
        
        try:
            out_path, _ = preprocess_subject(sid, nifti_path, atlas_img)
            processed_paths.append(out_path)
        except Exception as e:
            log_error(f"Skipping subject {sid} due to error: {e}")
            continue
    
    logger.info(f"Preprocessing pipeline complete. Processed {len(processed_paths)} subjects.")
    return processed_paths

def main():
    """CLI entry point for preprocessing."""
    import argparse
    parser = argparse.ArgumentParser(description="Preprocess HCP fMRI data with Schaefer atlas.")
    parser.add_argument("--subject", type=str, help="Specific subject ID to process.")
    parser.add_argument("--verify", action="store_true", help="Verify atlas download and run a test.")
    args = parser.parse_args()
    
    if args.verify:
        logger.info("Verifying atlas download...")
        try:
            img = load_schaefer_parcellation()
            logger.info(f"Atlas verification successful: {img.shape}")
        except Exception as e:
            logger.error(f"Atlas verification failed: {e}")
            return 1
        return 0
    
    if args.subject:
        # Process single subject
        raw_path = get_raw_path()
        # Heuristic to find the file
        subj_dir = os.path.join(raw_path, "HCP_1200", args.subject)
        if not os.path.exists(subj_dir):
            logger.error(f"Subject {args.subject} not found in {subj_dir}")
            return 1
        
        # Find NIfTI
        nifti_path = None
        for root, dirs, files in os.walk(subj_dir):
            for f in files:
                if (f.endswith('.nii') or f.endswith('.nii.gz')) and ('r' in f.lower() or 'func' in f.lower()):
                    nifti_path = os.path.join(root, f)
                    break
            if nifti_path: break
        
        if not nifti_path:
            logger.error(f"No NIfTI found for {args.subject}")
            return 1
        
        try:
            out_path, _ = preprocess_subject(args.subject, nifti_path)
            logger.info(f"Done. Output: {out_path}")
        except Exception as e:
            logger.error(f"Failed: {e}")
            return 1
    else:
        # Process all
        paths = run_preprocessing_pipeline()
        if not paths:
            logger.warning("No subjects processed.")
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())