import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import nibabel as nib
from nilearn import input_data
from nilearn.image import new_img_like
import networkx as nx
import bct

from src.utils.logging import get_logger, log_connectivity_computation

# Configure logging
logger = get_logger(__name__)

# Constants
SCHAEFER_200_URL = "https://raw.githubusercontent.com/Yeo-JLab/Yeo2011_Schaefer_2018/main/Schaefer2018_200Parcels_7Networks_order_FSLMNI152_res-2.nii.gz"
ATLAS_FILENAME = "Schaefer2018_200Parcels_7Networks_order_FSLMNI152_res-2.nii.gz"
FD_THRESHOLD = 0.5  # mm, used for exclusion logic if needed in pipeline

def load_schaefer_atlas(atlas_dir: Path) -> Tuple[np.ndarray, List[str]]:
    """
    Load the Schaefer 200-parcel atlas.
    
    If the atlas file exists locally, load it. Otherwise, attempt to download it.
    Returns the atlas image (Nifti1Image) and the list of region labels.
    """
    atlas_path = atlas_dir / ATLAS_FILENAME
    
    if not atlas_path.exists():
        logger.info(f"Atlas not found at {atlas_path}. Attempting download...")
        try:
            import urllib.request
            atlas_dir.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(SCHAEFER_200_URL, str(atlas_path))
            logger.info(f"Successfully downloaded atlas to {atlas_path}")
        except Exception as e:
            logger.error(f"Failed to download atlas: {e}")
            raise FileNotFoundError(f"Atlas file not found and download failed: {e}")
    
    # Load the NIfTI image
    atlas_img = nib.load(str(atlas_path))
    
    # Extract labels (parcels are 1-indexed in Schaefer atlas)
    # We assume the atlas has 200 regions labeled 1 to 200.
    # The labels can be derived from the unique values in the data.
    data = atlas_img.get_fdata()
    unique_labels = sorted(list(set(np.unique(data)) - {0}))
    
    # Create human-readable labels (Region 1, Region 2, ...) or use network info if available
    # For simplicity, we map 1..200 to "ROI_1".."ROI_200"
    # A more robust implementation would parse the README from the atlas repo.
    labels = [f"ROI_{int(label)}" for label in unique_labels]
    
    return atlas_img, labels

def extract_time_series(atlas_img: Any, fmri_img: Any, labels: List[str]) -> np.ndarray:
    """
    Extract the mean time series from each ROI defined by the atlas.
    
    Args:
        atlas_img: The Schaefer atlas NIfTI image.
        fmri_img: The preprocessed fMRI NIfTI image.
        labels: List of region labels (unused directly but kept for API consistency).
    
    Returns:
        np.ndarray: Time series array of shape (n_timepoints, n_regions).
    """
    # Use Nilearn's NiftiLabelsMasker
    masker = input_data.NiftiLabelsMasker(
        labels_img=atlas_img,
        standardize=True,  # Standardize time series (z-score)
        detrend=True,      # Detrend time series
        low_pass=None,     # Bandpass already done in preprocess
        high_pass=None,
        t_r=2.0,           # TR is typically 0.72 or 2.0 depending on dataset; HCP is 0.72
        memory="cache",
        verbose=0
    )
    
    try:
        time_series = masker.fit_transform(fmri_img)
    except Exception as e:
        logger.error(f"Failed to extract time series: {e}")
        raise
    
    return time_series

def compute_correlation_matrix(time_series: np.ndarray) -> np.ndarray:
    """
    Compute the Pearson correlation matrix from the time series.
    
    Args:
        time_series: Array of shape (n_timepoints, n_regions).
    
    Returns:
        np.ndarray: Correlation matrix of shape (n_regions, n_regions).
    """
    # Ensure time_series is float64 for precision
    ts = time_series.astype(np.float64)
    
    # Compute correlation matrix
    corr_matrix = np.corrcoef(ts, rowvar=False)
    
    # Handle potential NaNs (e.g., if a region has zero variance)
    if np.any(np.isnan(corr_matrix)):
        logger.warning("NaN values detected in correlation matrix. Filling with 0.")
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    return corr_matrix

def validate_connectivity_matrix(corr_matrix: np.ndarray, subject_id: str) -> Dict[str, Any]:
    """
    Validate the connectivity matrix for symmetry, diagonal, and range.
    
    Args:
        corr_matrix: The correlation matrix.
        subject_id: ID of the subject for logging.
    
    Returns:
        Dict containing validation results.
    """
    validation_result = {
        "subject_id": subject_id,
        "is_symmetric": False,
        "is_diagonal_one": False,
        "in_range": False,
        "shape": corr_matrix.shape,
        "errors": []
    }
    
    n = corr_matrix.shape[0]
    
    # Check shape (should be square)
    if corr_matrix.shape[0] != corr_matrix.shape[1]:
        validation_result["errors"].append("Matrix is not square.")
        return validation_result
    
    # Check symmetry (within floating point tolerance)
    if np.allclose(corr_matrix, corr_matrix.T):
        validation_result["is_symmetric"] = True
    else:
        validation_result["errors"].append("Matrix is not symmetric.")
    
    # Check diagonal (should be 1.0)
    diag = np.diag(corr_matrix)
    if np.allclose(diag, 1.0):
        validation_result["is_diagonal_one"] = True
    else:
        validation_result["errors"].append(f"Diagonal elements are not 1.0. Min: {diag.min()}, Max: {diag.max()}")
    
    # Check range [-1, 1]
    if corr_matrix.min() >= -1.0 and corr_matrix.max() <= 1.0:
        validation_result["in_range"] = True
    else:
        validation_result["errors"].append(f"Values out of range [-1, 1]. Min: {corr_matrix.min()}, Max: {corr_matrix.max()}")
    
    if not validation_result["is_symmetric"] or not validation_result["is_diagonal_one"] or not validation_result["in_range"]:
        logger.error(f"Validation failed for subject {subject_id}: {validation_result['errors']}")
        raise ValueError(f"Connectivity matrix validation failed for {subject_id}: {validation_result['errors']}")
    
    logger.info(f"Validation passed for subject {subject_id}. Shape: {n}x{n}")
    return validation_result

def save_connectivity_results(subject_id: str, corr_matrix: np.ndarray, output_dir: Path) -> Path:
    """
    Save the connectivity matrix and validation metadata to disk.
    
    Args:
        subject_id: Subject identifier.
        corr_matrix: The correlation matrix.
        output_dir: Directory to save results.
    
    Returns:
        Path to the saved matrix file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    matrix_path = output_dir / f"{subject_id}_connectivity.npy"
    meta_path = output_dir / f"{subject_id}_connectivity_meta.json"
    
    # Save matrix as .npy
    np.save(str(matrix_path), corr_matrix)
    
    # Save metadata
    meta_data = {
        "subject_id": subject_id,
        "matrix_shape": list(corr_matrix.shape),
        "matrix_min": float(corr_matrix.min()),
        "matrix_max": float(corr_matrix.max()),
        "matrix_mean": float(corr_matrix.mean()),
        "validation": {
            "is_symmetric": True,
            "is_diagonal_one": True,
            "in_range": True
        }
    }
    
    with open(meta_path, 'w') as f:
        json.dump(meta_data, f, indent=2)
    
    logger.info(f"Saved connectivity matrix for {subject_id} to {matrix_path}")
    return matrix_path

def process_subject(subject_id: str, fmri_path: Path, atlas_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Process a single subject: load atlas, extract time series, compute correlation, validate, and save.
    
    Args:
        subject_id: Subject identifier.
        fmri_path: Path to the preprocessed fMRI NIfTI file.
        atlas_dir: Directory containing the Schaefer atlas.
        output_dir: Directory to save results.
    
    Returns:
        Dict containing processing results and paths.
    """
    logger.info(f"Processing subject {subject_id}...")
    
    # 1. Load Atlas
    atlas_img, labels = load_schaefer_atlas(atlas_dir)
    
    # 2. Load fMRI
    if not fmri_path.exists():
        raise FileNotFoundError(f"fMRI file not found: {fmri_path}")
    fmri_img = nib.load(str(fmri_path))
    
    # 3. Extract Time Series
    time_series = extract_time_series(atlas_img, fmri_img, labels)
    logger.debug(f"Extracted time series shape: {time_series.shape}")
    
    # 4. Compute Correlation Matrix
    corr_matrix = compute_correlation_matrix(time_series)
    
    # 5. Validate
    validation = validate_connectivity_matrix(corr_matrix, subject_id)
    
    # 6. Save
    matrix_path = save_connectivity_results(subject_id, corr_matrix, output_dir)
    
    log_connectivity_computation(subject_id, matrix_path, time_series.shape, corr_matrix.shape)
    
    return {
        "subject_id": subject_id,
        "status": "success",
        "matrix_path": str(matrix_path),
        "time_series_shape": list(time_series.shape),
        "matrix_shape": list(corr_matrix.shape)
    }

def main():
    """
    Main entry point for the connectivity analysis pipeline.
    Expects subject IDs and file paths to be configured or passed via CLI/Env.
    For this implementation, we assume a standard directory structure:
    - data/preprocessed/<subject_id>_space-MNI_desc-preproc_bold.nii.gz
    - data/atlas/Schaefer2018_200Parcels_7Networks_order_FSLMNI152_res-2.nii.gz
    - data/connectivity/ (output)
    """
    # Setup paths
    base_dir = Path(os.getenv("DATA_PATH", "data"))
    atlas_dir = base_dir / "atlas"
    preprocessed_dir = base_dir / "preprocessed"
    output_dir = base_dir / "connectivity"
    
    # Ensure directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all preprocessed files
    fmri_files = list(preprocessed_dir.glob("*_desc-preproc_bold.nii.gz"))
    
    if not fmri_files:
        logger.warning(f"No preprocessed fMRI files found in {preprocessed_dir}")
        return
    
    logger.info(f"Found {len(fmri_files)} subjects to process.")
    
    results = []
    for fmri_file in fmri_files:
        subject_id = fmri_file.stem.replace("_desc-preproc_bold", "")
        # Handle potential variations in naming if necessary
        if not subject_id:
            subject_id = fmri_file.stem
        
        try:
            result = process_subject(subject_id, fmri_file, atlas_dir, output_dir)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process subject {subject_id}: {e}")
            results.append({
                "subject_id": subject_id,
                "status": "failed",
                "error": str(e)
            })
    
    # Save summary log
    summary_path = output_dir / "connectivity_run_log.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Connectivity analysis complete. Summary saved to {summary_path}")

if __name__ == "__main__":
    main()
