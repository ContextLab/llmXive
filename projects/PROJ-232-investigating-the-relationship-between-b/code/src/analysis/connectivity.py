"""
Connectivity analysis module for T013.

Loads preprocessed fMRI data, applies the Schaefer 200 atlas, extracts
time series, computes Pearson correlation matrices, and validates them.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import nibabel as nib
import pandas as pd
from nilearn import image, masking
from nilearn.datasets import fetch_atlas_schaefer_2018
from scipy.stats import pearsonr

# Import from project utilities
from src.utils.logging import get_logger, setup_experiment_logging

# Ensure project root is in path if running as script
if __name__ == "__main__":
    # Add parent of 'code' to path if needed, though usually handled by environment
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

logger = get_logger(__name__)


def load_schaefer_atlas(resolution: int = 2) -> Dict[str, Any]:
    """
    Fetch and load the Schaefer 2018 atlas (200 parcels, 7 networks).
    
    Args:
        resolution: MRI resolution in mm (default 2mm).
        
    Returns:
        Dictionary containing 'labels' (numpy array), 'maps' (nifti image),
        and 'networks' (list of network names).
    """
    logger.info(f"Fetching Schaefer 2018 atlas (resolution={resolution}mm)...")
    try:
        atlas_data = fetch_atlas_schaefer_2018(
            resolution=resolution,
            maps=True,
            yeo_networks=True,
            data_dir=str(Path(__file__).parents[2] / "data" / "external" / "atlas")
        )
    except Exception as e:
        logger.error(f"Failed to fetch Schaefer atlas: {e}")
        raise RuntimeError(f"Could not fetch Schaefer atlas: {e}")

    # atlas_data is a dict with keys: 'maps', 'labels', 'networks', etc.
    # 'maps' is the path to the NIfTI file
    # 'labels' is a numpy array of parcel names
    
    return {
        "maps_path": atlas_data['maps'],
        "labels": atlas_data['labels'],
        "networks": atlas_data['networks'] if 'networks' in atlas_data else [],
        "n_parcels": len(atlas_data['labels'])
    }


def extract_time_series(
    nifti_path: Path,
    atlas_path: Path,
    mask_path: Optional[Path] = None
) -> Tuple[np.ndarray, List[int]]:
    """
    Extract mean time series for each parcel in the Schaefer atlas.
    
    Args:
        nifti_path: Path to preprocessed 4D fMRI NIfTI file.
        atlas_path: Path to Schaefer atlas NIfTI file.
        mask_path: Optional path to a brain mask (if not provided, atlas is used as mask).
        
    Returns:
        Tuple of (time_series, parcel_indices) where time_series is (timepoints, n_parcels).
    """
    logger.info(f"Extracting time series from: {nifti_path}")
    logger.info(f"Using atlas: {atlas_path}")

    if not nifti_path.exists():
        raise FileNotFoundError(f"Preprocessed fMRI file not found: {nifti_path}")
    if not atlas_path.exists():
        raise FileNotFoundError(f"Atlas file not found: {atlas_path}")

    # Load images
    fmri_img = image.load_img(nifti_path)
    atlas_img = image.load_img(atlas_path)

    # Use the atlas as the mask (parcels define the regions)
    # nilearn's extract_roi can handle this if we treat the atlas as a label map
    # However, for mean time series per label, masking with the atlas is the standard approach
    # We use nilearn's signal extraction which handles label maps correctly
    
    try:
        # extract_labels_time_series handles label maps (integer values)
        # It returns a list of arrays, one per label
        time_series_list = masking.extract_labels_time_series(
            fmri_img,
            atlas_img,
            label_names=None, # We want all labels
            standardize=False,
            detrend=False,
            low_pass=None,
            high_pass=None,
            t_r=2.0 # Default TR, adjust if known from metadata
        )
    except Exception as e:
        logger.error(f"Error extracting time series: {e}")
        raise

    # Convert list of arrays to a single 2D array (timepoints, n_parcels)
    # The function returns a list where each element is (timepoints,)
    if not time_series_list:
        raise ValueError("No time series extracted. Check atlas and fMRI alignment.")
    
    n_timepoints = len(time_series_list[0])
    n_parcels = len(time_series_list)
    
    time_series = np.zeros((n_timepoints, n_parcels), dtype=np.float32)
    for i, ts in enumerate(time_series_list):
        time_series[:, i] = ts

    # Return parcel indices (1-based in atlas, 0-based in list)
    # The labels in the atlas are usually 1..N. We map them to indices.
    # extract_labels_time_series returns them in the order of unique labels found.
    # We need to be careful about the mapping if we need specific parcel IDs later.
    # For now, we assume the order corresponds to the sorted unique labels in the atlas.
    unique_labels = np.unique(atlas_img.get_fdata())
    # Filter out background (0)
    parcel_indices = [int(l) for l in unique_labels if l != 0]
    
    logger.info(f"Extracted {n_parcels} time series of length {n_timepoints}.")
    return time_series, parcel_indices


def compute_correlation_matrix(time_series: np.ndarray) -> np.ndarray:
    """
    Compute the Pearson correlation matrix from time series.
    
    Args:
        time_series: 2D array of shape (timepoints, n_parcels).
        
    Returns:
        2D array of shape (n_parcels, n_parcels).
    """
    logger.info("Computing Pearson correlation matrix...")
    n_parcels = time_series.shape[1]
    
    # Use numpy's corrcoef which returns (n_parcels, n_parcels)
    # It handles the normalization automatically
    corr_matrix = np.corrcoef(time_series, rowvar=False)
    
    if corr_matrix.shape != (n_parcels, n_parcels):
        raise ValueError(f"Correlation matrix shape {corr_matrix.shape} "
                         f"does not match expected ({n_parcels}, {n_parcels})")
        
    return corr_matrix


def validate_connectivity_matrix(
    matrix: np.ndarray,
    parcel_indices: List[int],
    expected_n_parcels: int = 200
) -> Dict[str, Any]:
    """
    Validate the connectivity matrix against schema criteria.
    
    Checks:
      1. Symmetry: matrix == matrix.T
      2. Diagonal: all 1.0 (or close to 1.0)
      3. Range: elements in [-1, 1]
      4. Shape: (N, N)
      
    Args:
        matrix: The correlation matrix.
        parcel_indices: List of parcel IDs corresponding to matrix rows/cols.
        expected_n_parcels: Expected number of parcels (default 200).
        
    Returns:
        Dictionary with validation results and status.
    """
    logger.info("Validating connectivity matrix...")
    issues = []
    is_valid = True

    # Check shape
    if matrix.shape[0] != matrix.shape[1]:
        issues.append(f"Matrix is not square: shape {matrix.shape}")
        is_valid = False
    elif matrix.shape[0] != expected_n_parcels:
        issues.append(f"Matrix size {matrix.shape[0]} != expected {expected_n_parcels}")
        # This might be a warning, but for strict validation we flag it
        # Depending on strictness, we might allow it if the atlas was smaller
        # For this task, we expect 200.
        if matrix.shape[0] < expected_n_parcels:
            is_valid = False
            issues.append(f"Missing parcels: expected {expected_n_parcels}, got {matrix.shape[0]}")

    n = matrix.shape[0]

    # Check symmetry
    if not np.allclose(matrix, matrix.T):
        max_diff = np.max(np.abs(matrix - matrix.T))
        issues.append(f"Matrix not symmetric (max diff: {max_diff:.2e})")
        is_valid = False

    # Check diagonal
    diag = np.diag(matrix)
    if not np.allclose(diag, 1.0, atol=1e-5):
        min_diag = np.min(diag)
        max_diag = np.max(diag)
        issues.append(f"Diagonal not all 1.0 (min: {min_diag:.4f}, max: {max_diag:.4f})")
        is_valid = False

    # Check range
    min_val = np.min(matrix)
    max_val = np.max(matrix)
    if min_val < -1.0 or max_val > 1.0:
        issues.append(f"Values out of range [-1, 1]: min={min_val:.4f}, max={max_val:.4f}")
        is_valid = False

    # Check for NaNs or Infs
    if np.any(np.isnan(matrix)):
        issues.append("Matrix contains NaN values")
        is_valid = False
    if np.any(np.isinf(matrix)):
        issues.append("Matrix contains Inf values")
        is_valid = False

    validation_result = {
        "is_valid": is_valid,
        "shape": list(matrix.shape),
        "min_value": float(min_val),
        "max_value": float(max_val),
        "diag_min": float(np.min(diag)),
        "diag_max": float(np.max(diag)),
        "is_symmetric": bool(np.allclose(matrix, matrix.T)),
        "issues": issues,
        "parcel_count": len(parcel_indices)
    }

    if is_valid:
        logger.info("Connectivity matrix validation PASSED.")
    else:
        logger.error(f"Connectivity matrix validation FAILED: {issues}")

    return validation_result


def save_connectivity_results(
    output_dir: Path,
    subject_id: str,
    matrix: np.ndarray,
    parcel_indices: List[int],
    validation_result: Dict[str, Any]
) -> Path:
    """
    Save the connectivity matrix and metadata to disk.
    
    Args:
        output_dir: Directory to save files.
        subject_id: Subject identifier.
        matrix: Correlation matrix.
        parcel_indices: List of parcel IDs.
        validation_result: Validation dictionary.
        
    Returns:
        Path to the saved JSON file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save matrix as CSV
    csv_path = output_dir / f"connectivity_{subject_id}.csv"
    df = pd.DataFrame(matrix)
    # Add parcel indices as column names and index
    df.columns = [f"parcel_{p}" for p in parcel_indices]
    df.index = [f"parcel_{p}" for p in parcel_indices]
    df.to_csv(csv_path)
    logger.info(f"Saved connectivity matrix to {csv_path}")

    # Save metadata and validation as JSON
    json_path = output_dir / f"connectivity_{subject_id}_meta.json"
    meta = {
        "subject_id": subject_id,
        "n_parcels": len(parcel_indices),
        "parcel_indices": parcel_indices,
        "validation": validation_result
    }
    with open(json_path, 'w') as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Saved metadata to {json_path}")

    return json_path


def process_subject(
    subject_id: str,
    fmri_path: Path,
    atlas_data: Dict[str, Any],
    output_dir: Path
) -> Dict[str, Any]:
    """
    Process a single subject: extract time series, compute correlation, validate, save.
    
    Args:
        subject_id: Subject identifier.
        fmri_path: Path to preprocessed fMRI NIfTI.
        atlas_data: Dictionary from load_schaefer_atlas.
        output_dir: Output directory for results.
        
    Returns:
        Dictionary with processing results and status.
    """
    logger.info(f"Processing subject: {subject_id}")
    
    try:
        # Load atlas
        atlas_img = image.load_img(atlas_data['maps_path'])
        
        # Extract time series
        time_series, parcel_indices = extract_time_series(fmri_path, atlas_data['maps_path'])
        
        # Compute correlation
        matrix = compute_correlation_matrix(time_series)
        
        # Validate
        validation = validate_connectivity_matrix(matrix, parcel_indices)
        
        # Save
        if validation['is_valid']:
            save_connectivity_results(output_dir, subject_id, matrix, parcel_indices, validation)
            return {
                "subject_id": subject_id,
                "status": "success",
                "validation": validation,
                "output_files": [
                    str(output_dir / f"connectivity_{subject_id}.csv"),
                    str(output_dir / f"connectivity_{subject_id}_meta.json")
                ]
            }
        else:
            # Even if invalid, we might want to log it, but task implies we only save valid ones?
            # The task says "Validate symmetry and diagonal". If it fails, we should probably
            # not produce the final artifact or mark it as failed.
            logger.warning(f"Subject {subject_id} produced invalid matrix. Not saving.")
            return {
                "subject_id": subject_id,
                "status": "failed",
                "validation": validation,
                "error": "Validation failed"
            }
            
    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {e}")
        return {
            "subject_id": subject_id,
            "status": "error",
            "error": str(e)
        }


def main():
    """
    Main entry point for connectivity analysis.
    
    Expects preprocessed data in data/preprocessed/ and outputs to data/connectivity/.
    """
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    preprocessed_dir = data_dir / "preprocessed"
    output_dir = data_dir / "connectivity"
    
    # Setup logging
    setup_experiment_logging("connectivity_analysis")
    
    logger.info("Starting connectivity analysis pipeline (T013).")
    
    # 1. Load Atlas
    atlas_data = load_schaefer_atlas(resolution=2)
    logger.info(f"Atlas loaded: {atlas_data['n_parcels']} parcels.")
    
    if atlas_data['n_parcels'] != 200:
        logger.warning(f"Expected 200 parcels, got {atlas_data['n_parcels']}. "
                       "Proceeding with available parcels.")
    
    # 2. Find preprocessed subjects
    # Expected structure: data/preprocessed/<subject_id>/sub-<id>_desc-preproc_bold.nii.gz
    # Or similar pattern defined in T012d
    if not preprocessed_dir.exists():
        logger.error(f"Preprocessed directory not found: {preprocessed_dir}")
        sys.exit(1)
        
    subjects = []
    for item in preprocessed_dir.iterdir():
        if item.is_dir():
            # Look for fMRI files
            # Pattern: sub-<id>_desc-preproc_bold.nii.gz or similar
            fmri_files = list(item.glob("*_desc-preproc_bold.nii.gz"))
            if not fmri_files:
                # Try other common patterns
                fmri_files = list(item.glob("func/*_space-MNI_desc-preproc_bold.nii.gz"))
            
            if fmri_files:
                subjects.append({
                    "id": item.name.replace("sub-", "").replace("_", ""), # Simple extraction
                    "fmri_path": fmri_files[0]
                })
            else:
                # Check for any nifti in func
                func_dir = item / "func"
                if func_dir.exists():
                    niftis = list(func_dir.glob("*.nii.gz"))
                    if niftis:
                        subjects.append({
                            "id": item.name.replace("sub-", "").replace("_", ""),
                            "fmri_path": niftis[0]
                        })
    
    if not subjects:
        logger.error("No preprocessed subjects found in data/preprocessed/")
        sys.exit(1)
        
    logger.info(f"Found {len(subjects)} subjects to process.")
    
    # 3. Process each subject
    results = []
    for sub in subjects:
        res = process_subject(
            sub["id"],
            sub["fmri_path"],
            atlas_data,
            output_dir
        )
        results.append(res)
    
    # 4. Summary
    success_count = sum(1 for r in results if r["status"] == "success")
    fail_count = sum(1 for r in results if r["status"] == "failed")
    error_count = sum(1 for r in results if r["status"] == "error")
    
    logger.info(f"Processing complete. Success: {success_count}, Failed: {fail_count}, Errors: {error_count}")
    
    # Save run log
    log_path = output_dir / "connectivity_run_log.json"
    with open(log_path, 'w') as f:
        json.dump({
            "total_subjects": len(subjects),
            "success": success_count,
            "failed": fail_count,
            "errors": error_count,
            "results": results
        }, f, indent=2)
    
    if error_count > 0 or fail_count > 0:
        logger.warning("Some subjects failed processing. Check logs.")
        # Do not exit with error unless ALL failed? The task implies we produce outputs for valid ones.
        # But if the pipeline is meant to be robust, we might just log.
        # For now, we assume partial success is acceptable as long as valid outputs exist.
        
    logger.info("Connectivity analysis finished.")


if __name__ == "__main__":
    main()