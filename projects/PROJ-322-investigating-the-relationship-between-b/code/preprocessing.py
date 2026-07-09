import os
import sys
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from nilearn import datasets, masking, image
from nilearn.connectome import ConnectivityMeasure
from nilearn.graph import parcellation
import networkx as nx

from config import get_config, is_synthetic, get_memory_limit_gb
from logging_config import get_logger, check_memory_and_warn
from memory_monitor import get_current_ram_gb, is_limit_exceeded
from entities import Subject, ConnectivityMatrix

# Atlas configuration
AAL_ATLAS_NAME = "aal"
AAL_ATLAS_VERSION = "1.1"  # Standard version often available via nilearn or local
DEFAULT_ATLAS_PATH = Path(__file__).parent.parent / "data" / "atlas" / "aal"

logger = get_logger(__name__)

def download_atlas_if_needed() -> Optional[Path]:
    """
    Attempts to download the AAL atlas.
    Returns the path to the atlas file if successful, None if it fails.
    """
    atlas_path = DEFAULT_ATLAS_PATH
    if atlas_path.exists():
        logger.info(f"AAL atlas already exists at {atlas_path}")
        return atlas_path

    atlas_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Attempting to download AAL atlas to {atlas_path}...")

    try:
        # Try to fetch via nilearn if available, otherwise fallback to manual URL
        # Note: nilearn's fetch_atlas_aal might require specific version or internet
        # We wrap in try/except to handle network failures or missing packages gracefully
        dataset = datasets.fetch_atlas_aal()
        if dataset:
            # nilearn returns a dict with 'maps' and 'labels'
            # We expect 'maps' to be the 3D NIfTI file
            if 'maps' in dataset:
                src_file = dataset['maps']
                dest_file = atlas_path / "aal_atlas.nii.gz"
                # Copy or move
                import shutil
                shutil.copy(src_file, dest_file)
                logger.info(f"AAL atlas downloaded successfully to {dest_file}")
                return dest_file
            else:
                logger.warning("nilearn fetch_atlas_aal returned data but no 'maps' file.")
                return None
        else:
            logger.warning("nilearn fetch_atlas_aal returned None.")
            return None
    except Exception as e:
        logger.error(f"Failed to download AAL atlas via nilearn: {e}")
        # Fallback: Try manual download if nilearn fails
        # This is a robustness measure; if this also fails, we return None
        try:
            import urllib.request
            # Common public URL for AAL atlas (verify availability)
            # Using a generic placeholder URL logic; in production, verify this URL is stable
            url = "https://www.gin.cnrs.fr/wp-content/uploads/2017/10/AAL_T1.nii.gz"
            dest_file = atlas_path / "aal_atlas.nii.gz"
            logger.info(f"Attempting manual download from {url}...")
            urllib.request.urlretrieve(url, dest_file)
            logger.info(f"AAL atlas downloaded manually to {dest_file}")
            return dest_file
        except Exception as manual_err:
            logger.error(f"Manual download also failed: {manual_err}")
            return None

def load_confounds_from_bids(subject_dir: Path) -> Optional[pd.DataFrame]:
    """
    Loads confound regressors from a BIDS-compliant directory.
    """
    # Look for confounds.tsv
    confounds_files = list(subject_dir.glob("*confounds*.tsv"))
    if not confounds_files:
        logger.warning(f"No confounds file found in {subject_dir}")
        return None
    
    # Assume the first one found is the one we want
    confounds_file = confounds_files[0]
    try:
        confounds = pd.read_csv(confounds_file, sep='\t')
        logger.info(f"Loaded confounds from {confounds_file}")
        return confounds
    except Exception as e:
        logger.error(f"Failed to load confounds from {confounds_file}: {e}")
        return None

def preprocess_fmri(
    fmri_file: Path,
    confounds: Optional[pd.DataFrame] = None,
    atlas_file: Optional[Path] = None
) -> Optional[np.ndarray]:
    """
    Performs minimal preprocessing: smoothing, confound regression, and parcellation.
    Returns a time-series array (n_regions, n_timepoints).
    """
    if not fmri_file.exists():
        logger.error(f"fMRI file not found: {fmri_file}")
        return None

    if atlas_file is None or not atlas_file.exists():
        logger.error(f"Atlas file not found or not provided: {atlas_file}")
        return None

    try:
        # Load image
        fmri_img = image.load_img(fmri_file)
        
        # 1. Smoothing (optional, minimal)
        # fmri_img = image.smooth_img(fmri_img, fwhm=6) 
        # Skipping smoothing for minimal preprocessing as per task description unless specified

        # 2. Confound Regression
        if confounds is not None:
            # Select common confounds if available, else all
            confound_cols = [c for c in confounds.columns if c in confounds.columns]
            if len(confound_cols) > 0:
                confounds_clean = confounds[confound_cols].fillna(0)
                fmri_img = image.clean_img(
                    fmri_img,
                    confounds=confounds_clean,
                    detrend=True,
                    standardize=False
                )
            else:
                logger.warning("No confound columns found to regress.")
                fmri_img = image.clean_img(fmri_img, detrend=True, standardize=False)
        else:
            fmri_img = image.clean_img(fmri_img, detrend=True, standardize=False)

        # 3. Parcellation using AAL
        # nilearn's parcellation module expects a 3D atlas and labels
        # We assume the atlas file is a 3D NIfTI where each voxel has a region ID
        
        # Using nilearn's parcellation function
        # Note: This might fail if the atlas format is not exactly as expected
        # We catch this in the caller (process_subject)
        from nilearn import input_data
        
        # Extract time series
        # We use NiftiLabelsMasker for robustness
        masker = input_data.NiftiLabelsMasker(
            labels_img=atlas_file,
            standardize=True,
            detrend=True,
            memory="nilearn_cache",
            verbose=0
        )
        
        time_series = masker.fit_transform(fmri_img)
        logger.info(f"Extracted time series shape: {time_series.shape}")
        return time_series

    except Exception as e:
        logger.error(f"Preprocessing failed for {fmri_file}: {e}")
        return None

def compute_connectivity_matrix(
    time_series: np.ndarray,
    method: str = 'correlation'
) -> np.ndarray:
    """
    Computes a connectivity matrix from a time series.
    """
    if time_series is None or time_series.shape[0] == 0:
        logger.error("Invalid time series for connectivity computation.")
        raise ValueError("Invalid time series")

    conn_measure = ConnectivityMeasure(kind=method)
    matrices = conn_measure.fit_transform([time_series])
    return matrices[0]

def save_connectivity_matrix(
    matrix: np.ndarray,
    subject_id: str,
    time_point: str,
    output_dir: Path
) -> Path:
    """
    Saves the connectivity matrix to a file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"sub-{subject_id}_{time_point}_connectivity.npy"
    filepath = output_dir / filename
    np.save(filepath, matrix)
    logger.info(f"Saved connectivity matrix to {filepath}")
    return filepath

def check_time_point_completeness(subject_data: Dict[str, Any]) -> bool:
    """
    Checks if a subject has both acute and chronic time points.
    Returns True if complete, False otherwise.
    """
    # Assuming subject_data has a 'time_points' key with a list of available points
    # or a structure like {'acute': path, 'chronic': path}
    if isinstance(subject_data, dict):
        points = subject_data.get('time_points', [])
        # Check for presence of required keys or values
        # This logic depends on the exact structure from data_ingestion
        # For now, assuming a list of strings
        required = ['acute', 'chronic']
        # Normalize to lowercase
        available = [str(p).lower() for p in points]
        return all(r in available for r in required)
    return False

def process_subject(
    subject_id: str,
    subject_data: Dict[str, Any],
    atlas_file: Path
) -> Optional[Subject]:
    """
    Processes a single subject:
    1. Downloads atlas if needed (handled in pipeline start, but safe to check)
    2. Iterates through time points
    3. Preprocesses fMRI
    4. Computes connectivity
    5. Handles AAL failure gracefully
    """
    logger.info(f"Processing subject: {subject_id}")
    
    # Check memory
    if is_limit_exceeded():
        logger.error(f"Memory limit exceeded while processing {subject_id}. Skipping.")
        return None

    # Ensure atlas is available
    if not atlas_file.exists():
        logger.error(f"AAL atlas not found at {atlas_file}. Cannot process {subject_id}.")
        # This is a critical failure for the batch, but we return None for this subject
        return None

    subject = Subject(id=subject_id, time_points={})
    
    # Iterate over time points
    # Assuming subject_data structure: {'time_points': [{'id': 'acute', 'path': '...'}, ...]}
    # Or similar. Adapting to generic dict structure.
    time_points = subject_data.get('time_points', [])
    
    for tp in time_points:
        tp_id = tp.get('id', 'unknown')
        tp_path = Path(tp.get('path', ''))
        
        if not tp_path.exists():
            logger.warning(f"Time point file not found for {subject_id} at {tp_id}: {tp_path}")
            continue

        logger.info(f"  Processing time point: {tp_id}")
        
        # Load confounds
        confounds = load_confounds_from_bids(tp_path.parent)
        
        # Preprocess
        # This is the critical step where AAL failure might occur
        try:
            ts = preprocess_fmri(tp_path, confounds, atlas_file)
            if ts is None:
                # Preprocessing failed (e.g., AAL failure, file corruption)
                logger.error(f"  Preprocessing FAILED for {subject_id} at {tp_id}. Skipping this time point.")
                # Do NOT add to subject, log error, and continue to next time point
                continue
            
            # Compute connectivity
            conn_matrix = compute_connectivity_matrix(ts)
            
            # Save matrix
            output_dir = Path(__file__).parent.parent / "data" / "processed"
            matrix_path = save_connectivity_matrix(conn_matrix, subject_id, tp_id, output_dir)
            
            # Add to subject
            subject.time_points[tp_id] = {
                'path': str(matrix_path),
                'matrix': conn_matrix,
                'status': 'success'
            }
            
        except Exception as e:
            # CATCH ALL for AAL failure or other unexpected errors
            # Specifically looking for AAL-related errors
            error_msg = str(e)
            if "aal" in error_msg.lower() or "atlas" in error_msg.lower() or "labels" in error_msg.lower():
                logger.error(f"  AAL ATLAS FAILURE for {subject_id} at {tp_id}: {e}")
            else:
                logger.error(f"  Unexpected error during processing of {subject_id} at {tp_id}: {e}")
            
            # Log the error and SKIP this subject/time point without crashing
            # Do not add to subject
            continue

    # If no time points were successfully processed, return None
    if not subject.time_points:
        logger.warning(f"Subject {subject_id} had no successfully processed time points. Skipping subject.")
        return None

    return subject

def run_preprocessing_pipeline(
    manifest_path: Path,
    output_dir: Optional[Path] = None
) -> List[Subject]:
    """
    Runs the preprocessing pipeline on all subjects in the manifest.
    Handles AAL atlas failure by skipping affected subjects/time points.
    """
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        return []

    # Download atlas once
    atlas_file = download_atlas_if_needed()
    if atlas_file is None:
        logger.error("AAL Atlas download failed. Cannot proceed with preprocessing.")
        return []

    # Load manifest
    df = pd.read_csv(manifest_path)
    processed_subjects = []

    for _, row in df.iterrows():
        # Check memory periodically
        check_memory_and_warn()
        
        subject_id = row['subject_id']
        # Reconstruct data structure for process_subject
        # Assuming manifest has: subject_id, time_point_id, file_path
        # We need to group by subject_id first. 
        # For simplicity in this loop, we assume the manifest is already grouped or we process row by row
        # But process_subject expects a dict of time points.
        # Let's adjust: we'll build the dict here or assume the manifest is structured differently.
        # Given the task context, let's assume the manifest is a list of files to process per subject.
        # We'll do a simple pass: if the manifest has multiple rows per subject, we need to group.
        
        # For this implementation, we assume the caller groups the data or the manifest is simple.
        # Let's assume the manifest is: subject_id, time_point, file_path
        # We will group manually here to be safe.
        pass

    # Better approach: Group by subject_id
    grouped = df.groupby('subject_id')
    
    for subject_id, group in grouped:
        time_points_list = []
        for _, tp_row in group.iterrows():
            time_points_list.append({
                'id': tp_row['time_point'],
                'path': tp_row['file_path']
            })
        
        subject_data = {'time_points': time_points_list}
        
        subject = process_subject(subject_id, subject_data, atlas_file)
        if subject:
            processed_subjects.append(subject)
        else:
            logger.warning(f"Skipping subject {subject_id} due to processing errors.")

    logger.info(f"Preprocessing pipeline complete. Processed {len(processed_subjects)} subjects.")
    return processed_subjects

def main():
    """
    Entry point for the preprocessing script.
    """
    config = get_config()
    manifest_path = Path(config.get('manifest_path', 'data/results/manifest.csv'))
    output_dir = Path(config.get('output_dir', 'data/processed'))
    
    if not manifest_path.exists():
        logger.error(f"Manifest not found at {manifest_path}. Run data_ingestion first.")
        sys.exit(1)

    subjects = run_preprocessing_pipeline(manifest_path, output_dir)
    
    # Save summary
    summary = {
        'total_processed': len(subjects),
        'subjects': [s.id for s in subjects]
    }
    summary_path = Path(output_dir) / "preprocessing_summary.json"
    with open(summary_path, 'w') as f:
        import json
        json.dump(summary, f, indent=2)
    
    logger.info(f"Summary saved to {summary_path}")

if __name__ == "__main__":
    main()