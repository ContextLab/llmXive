import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import nibabel as nib
from nilearn import datasets, masking
from nilearn.image import new_img_like
import networkx as nx

from src.utils.logging import get_logger
from src.config.env_config import get_data_path

logger = get_logger(__name__)

# Constants for Schaefer Atlas (200 parcels, 7 networks)
SCHAEFER_200_URL = (
    "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/v0.14.3/"
    "stable_examples/BrainParcellation/Schaefer2018_LocalGlobal/"
    "Parcellations/MNI/Schaefer2018_200Parcels_7Networks_order_FSLMNI152_2mm.nii.gz"
)
SCHAEFER_200_LABELS_URL = (
    "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/v0.14.3/"
    "stable_examples/BrainParcellation/Schaefer2018_LocalGlobal/"
    "Parcellations/MNI/Schaefer2018_200Parcels_7Networks_order.txt"
)

def load_schaefer_atlas(cache_dir: Optional[Path] = None) -> Tuple[nib.Nifti1Image, List[str]]:
    """
    Downloads and loads the Schaefer 200-parcel atlas.
    
    Returns:
        Tuple of (atlas image, list of parcel labels in order)
    """
    if cache_dir is None:
        cache_dir = Path.home() / ".cache" / "nilearn" / "yeo"
        
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    atlas_path = cache_dir / "schaefer_200.nii.gz"
    labels_path = cache_dir / "schaefer_200_labels.txt"
    
    # Download atlas if not present
    if not atlas_path.exists():
        logger.info(f"Downloading Schaefer 200 atlas to {atlas_path}")
        try:
            import requests
            response = requests.get(SCHAEFER_200_URL, stream=True)
            response.raise_for_status()
            with open(atlas_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        except Exception as e:
            logger.error(f"Failed to download atlas: {e}")
            raise RuntimeError(f"Could not download Schaefer atlas: {e}")
    
    # Download labels if not present
    if not labels_path.exists():
        logger.info(f"Downloading Schaefer 200 labels to {labels_path}")
        try:
            import requests
            response = requests.get(SCHAEFER_200_LABELS_URL, stream=True)
            response.raise_for_status()
            with open(labels_path, 'w') as f:
                f.write(response.text)
        except Exception as e:
            logger.error(f"Failed to download labels: {e}")
            raise RuntimeError(f"Could not download Schaefer labels: {e}")
    
    # Load atlas image
    atlas_img = nib.load(atlas_path)
    
    # Load labels
    labels = []
    with open(labels_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Format: "1\tDMN\t..." or "1\t1\t..."
                parts = line.split('\t')
                if len(parts) >= 2:
                    # Take the network name or parcel name
                    labels.append(parts[1] if parts[1] else f"Parcel_{parts[0]}")
                else:
                    labels.append(f"Parcel_{line}")
    
    if len(labels) != 200:
        logger.warning(f"Expected 200 labels, got {len(labels)}. Using indices.")
        labels = [f"Parcel_{i}" for i in range(200)]
    
    return atlas_img, labels

def extract_time_series(
    fmri_img_path: Path,
    atlas_img: nib.Nifti1Image,
    labels: List[str]
) -> np.ndarray:
    """
    Extracts mean time series from each parcel in the Schaefer atlas.
    
    Args:
        fmri_img_path: Path to preprocessed fMRI NIfTI file
        atlas_img: Schaefer atlas image
        labels: List of parcel labels
        
    Returns:
        2D array of shape (n_timepoints, 200)
    """
    if not fmri_img_path.exists():
        raise FileNotFoundError(f"fMRI image not found: {fmri_img_path}")
    
    logger.info(f"Extracting time series from {fmri_img_path}")
    
    fmri_img = nib.load(fmri_img_path)
    
    # Ensure atlas and fMRI are in same space (resample atlas to fMRI if needed)
    if atlas_img.shape != fmri_img.shape:
        logger.info("Resampling atlas to fMRI space...")
        from nilearn.image import resample_to_img
        atlas_img = resample_to_img(atlas_img, fmri_img, interpolation='nearest')
    
    # Get mask of brain (non-zero in atlas)
    atlas_data = atlas_img.get_fdata()
    mask = atlas_data > 0
    
    # Extract time series using Nilearn's NiftiLabelsMasker
    # We need to create a proper labels masker
    from nilearn.input_data import NiftiLabelsMasker
    
    masker = NiftiLabelsMasker(
        labels_img=atlas_img,
        labels=range(1, 201),  # 1-indexed
        standardize=True,
        detrend=True,
        memory='nilearn_cache',
        memory_level=1,
        verbose=0
    )
    
    time_series = masker.fit_transform(fmri_img)
    
    logger.info(f"Extracted time series shape: {time_series.shape}")
    return time_series

def compute_correlation_matrix(time_series: np.ndarray) -> np.ndarray:
    """
    Computes Pearson correlation matrix from time series.
    
    Args:
        time_series: 2D array of shape (n_timepoints, n_regions)
        
    Returns:
        2D array of shape (n_regions, n_regions) correlation matrix
    """
    logger.info("Computing Pearson correlation matrix...")
    
    if time_series.ndim != 2:
        raise ValueError(f"Expected 2D time series, got {time_series.ndim}D")
    
    # Use numpy's corrcoef
    corr_matrix = np.corrcoef(time_series.T)
    
    logger.info(f"Correlation matrix shape: {corr_matrix.shape}")
    return corr_matrix

def validate_connectivity_matrix(
    corr_matrix: np.ndarray,
    labels: List[str]
) -> Dict[str, Any]:
    """
    Validates the connectivity matrix for symmetry, diagonal, and value range.
    
    Args:
        corr_matrix: Correlation matrix
        labels: Parcel labels
        
    Returns:
        Dict with validation results
    """
    logger.info("Validating connectivity matrix...")
    
    n_regions = corr_matrix.shape[0]
    expected_shape = (len(labels), len(labels))
    
    validation = {
        "is_valid": True,
        "shape_correct": corr_matrix.shape == expected_shape,
        "is_symmetric": True,
        "diagonal_is_one": True,
        "values_in_range": True,
        "issues": []
    }
    
    # Check shape
    if not validation["shape_correct"]:
        validation["is_valid"] = False
        validation["issues"].append(f"Shape {corr_matrix.shape} != {expected_shape}")
    
    # Check symmetry
    if not np.allclose(corr_matrix, corr_matrix.T):
        validation["is_valid"] = False
        validation["is_symmetric"] = False
        max_diff = np.max(np.abs(corr_matrix - corr_matrix.T))
        validation["issues"].append(f"Matrix not symmetric, max diff: {max_diff:.6f}")
    
    # Check diagonal (should be 1.0)
    diagonal = np.diag(corr_matrix)
    if not np.allclose(diagonal, 1.0):
        validation["is_valid"] = False
        validation["diagonal_is_one"] = False
        mean_diag = np.mean(diagonal)
        validation["issues"].append(f"Diagonal not 1.0, mean: {mean_diag:.6f}")
    
    # Check value range [-1, 1]
    if np.any(corr_matrix < -1.0) or np.any(corr_matrix > 1.0):
        validation["is_valid"] = False
        validation["values_in_range"] = False
        min_val = np.min(corr_matrix)
        max_val = np.max(corr_matrix)
        validation["issues"].append(f"Values out of range: [{min_val:.4f}, {max_val:.4f}]")
    
    if validation["is_valid"]:
        logger.info("Connectivity matrix validation PASSED")
    else:
        logger.warning(f"Connectivity matrix validation FAILED: {validation['issues']}")
    
    return validation

def save_connectivity_results(
    output_dir: Path,
    subject_id: str,
    corr_matrix: np.ndarray,
    labels: List[str],
    validation: Dict[str, Any]
) -> Dict[str, str]:
    """
    Saves connectivity matrix and metadata to disk.
    
    Args:
        output_dir: Output directory
        subject_id: Subject identifier
        corr_matrix: Correlation matrix
        labels: Parcel labels
        validation: Validation results
        
    Returns:
        Dict of output file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save matrix as numpy file
    matrix_path = output_dir / f"{subject_id}_connectivity.npy"
    np.save(matrix_path, corr_matrix)
    
    # Save labels
    labels_path = output_dir / f"{subject_id}_labels.json"
    with open(labels_path, 'w') as f:
        json.dump({"labels": labels, "n_regions": len(labels)}, f, indent=2)
    
    # Save validation report
    validation_path = output_dir / f"{subject_id}_validation.json"
    with open(validation_path, 'w') as f:
        json.dump(validation, f, indent=2)
    
    # Save full results
    results_path = output_dir / f"{subject_id}_results.json"
    results = {
        "subject_id": subject_id,
        "matrix_shape": list(corr_matrix.shape),
        "matrix_min": float(np.min(corr_matrix)),
        "matrix_max": float(np.max(corr_matrix)),
        "matrix_mean": float(np.mean(corr_matrix)),
        "validation": validation,
        "output_files": {
            "matrix": str(matrix_path),
            "labels": str(labels_path),
            "validation": str(validation_path)
        }
    }
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved connectivity results for {subject_id}")
    return results["output_files"]

def process_subject(
    subject_id: str,
    fmri_path: Path,
    output_dir: Path,
    cache_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Processes a single subject: loads atlas, extracts time series, computes correlation.
    
    Args:
        subject_id: Subject identifier
        fmri_path: Path to preprocessed fMRI NIfTI
        output_dir: Directory to save results
        cache_dir: Directory for atlas cache
        
    Returns:
        Processing results dict
    """
    logger.info(f"Processing subject: {subject_id}")
    
    # Load atlas
    atlas_img, labels = load_schaefer_atlas(cache_dir)
    
    # Extract time series
    time_series = extract_time_series(fmri_path, atlas_img, labels)
    
    # Compute correlation matrix
    corr_matrix = compute_correlation_matrix(time_series)
    
    # Validate
    validation = validate_connectivity_matrix(corr_matrix, labels)
    
    if not validation["is_valid"]:
        logger.error(f"Validation failed for {subject_id}: {validation['issues']}")
        # Still save for debugging, but mark as invalid
    
    # Save results
    output_files = save_connectivity_results(output_dir, subject_id, corr_matrix, labels, validation)
    
    return {
        "subject_id": subject_id,
        "success": validation["is_valid"],
        "time_series_shape": list(time_series.shape),
        "matrix_shape": list(corr_matrix.shape),
        "validation": validation,
        "output_files": output_files
    }

def main():
    """
    Main entry point for running connectivity analysis on all subjects.
    
    Reads subject list from data/preprocessing/run_log.json, processes each,
    and writes a summary to data/analysis/connectivity_summary.json.
    """
    logger.info("Starting connectivity analysis pipeline")
    
    # Get paths
    data_path = get_data_path()
    preprocessing_log = Path(data_path) / "preprocessing" / "run_log.json"
    output_dir = Path(data_path) / "connectivity"
    
    if not preprocessing_log.exists():
        logger.error(f"Preprocessing log not found: {preprocessing_log}")
        sys.exit(1)
    
    # Load preprocessing log
    with open(preprocessing_log, 'r') as f:
        log_data = json.load(f)
    
    subjects = log_data.get("subjects", [])
    if not subjects:
        logger.error("No subjects found in preprocessing log")
        sys.exit(1)
    
    results = []
    successful = 0
    failed = 0
    
    for subject_info in subjects:
        subject_id = subject_info.get("id")
        fmri_path = Path(subject_info.get("preprocessed_nifti"))
        
        if not subject_id or not fmri_path.exists():
            logger.warning(f"Skipping invalid subject: {subject_info}")
            failed += 1
            continue
        
        try:
            result = process_subject(
                subject_id=subject_id,
                fmri_path=fmri_path,
                output_dir=output_dir
            )
            results.append(result)
            if result["success"]:
                successful += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Error processing {subject_id}: {e}")
            results.append({
                "subject_id": subject_id,
                "success": False,
                "error": str(e)
            })
            failed += 1
    
    # Write summary
    summary = {
        "total_subjects": len(subjects),
        "successful": successful,
        "failed": failed,
        "results": results
    }
    
    summary_path = output_dir / "connectivity_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Connectivity analysis complete. Summary: {summary_path}")
    
    if failed > 0:
        logger.warning(f"{failed} subjects failed processing")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
