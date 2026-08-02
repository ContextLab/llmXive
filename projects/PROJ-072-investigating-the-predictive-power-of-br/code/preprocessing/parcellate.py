"""
Parcellation module for AAL atlas-based connectivity matrix generation.

This module handles:
1. Loading the AAL atlas (90 regions)
2. Extracting region-wise time series from preprocessed fMRI data
3. Computing Pearson correlation matrices
4. Saving connectivity matrices to disk
"""
import os
import sys
import numpy as np
import nibabel as nib
from pathlib import Path
import logging
from typing import Tuple, List, Optional

# Project imports
from preprocessing.psd_validator import validate_and_regularize_matrix

# Configure logging
logger = logging.getLogger(__name__)

# Constants
AAL_ATLAS_URL = "https://raw.githubusercontent.com/nilearn/nilearn/main/nilearn/datasets/data/aal/AAL.nii"
AAL_LABELS_URL = "https://raw.githubusercontent.com/nilearn/nilearn/main/nilearn/datasets/data/aal/AAL_labels.txt"
DEFAULT_AAL_PATH = Path("data/raw/aal/AAL.nii")
DEFAULT_LABELS_PATH = Path("data/raw/aal/AAL_labels.txt")
MATRIX_OUTPUT_DIR = Path("data/processed")
MATRIX_DIMENSION = 90  # AAL atlas has 90 regions

def get_aal_atlas_path(force_download: bool = False) -> Path:
    """
    Get the path to the AAL atlas file. Downloads if missing.

    Args:
        force_download: If True, re-download even if file exists.

    Returns:
        Path to the AAL atlas NIfTI file.

    Raises:
        FileNotFoundError: If download fails and file doesn't exist.
    """
    atlas_path = DEFAULT_AAL_PATH
    labels_path = DEFAULT_LABELS_PATH

    # Ensure directories exist
    atlas_path.parent.mkdir(parents=True, exist_ok=True)

    # Download atlas if missing or forced
    if force_download or not atlas_path.exists():
        logger.info(f"Downloading AAL atlas to {atlas_path}")
        import requests
        try:
            response = requests.get(AAL_ATLAS_URL, timeout=30)
            response.raise_for_status()
            with open(atlas_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Successfully downloaded AAL atlas")
        except Exception as e:
            if atlas_path.exists():
                logger.warning(f"Download failed but file exists: {e}. Using existing file.")
            else:
                raise FileNotFoundError(f"Failed to download AAL atlas and no local file found: {e}")

    if force_download or not labels_path.exists():
        logger.info(f"Downloading AAL labels to {labels_path}")
        import requests
        try:
            response = requests.get(AAL_LABELS_URL, timeout=30)
            response.raise_for_status()
            with open(labels_path, 'w') as f:
                f.write(response.text)
            logger.info(f"Successfully downloaded AAL labels")
        except Exception as e:
            if labels_path.exists():
                logger.warning(f"Download failed but file exists: {e}. Using existing file.")
            else:
                raise FileNotFoundError(f"Failed to download AAL labels and no local file found: {e}")

    return atlas_path

def load_parcellation_labels(labels_path: Optional[Path] = None) -> List[str]:
    """
    Load AAL region labels.

    Args:
        labels_path: Path to labels file. Uses default if None.

    Returns:
        List of region names.
    """
    if labels_path is None:
        labels_path = DEFAULT_LABELS_PATH

    if not labels_path.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_path}")

    with open(labels_path, 'r') as f:
        # Skip header if present, read region names
        lines = [line.strip() for line in f if line.strip()]
        # AAL labels file typically has format: "1:RegionName"
        # We extract just the region names
        labels = []
        for line in lines:
            if ':' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    labels.append(parts[1].strip())
            else:
                labels.append(line.strip())

    # Ensure we have exactly 90 labels
    if len(labels) < MATRIX_DIMENSION:
        # Pad with generic names if needed
        while len(labels) < MATRIX_DIMENSION:
            labels.append(f"Region_{len(labels)+1}")
    elif len(labels) > MATRIX_DIMENSION:
        labels = labels[:MATRIX_DIMENSION]

    return labels

def extract_region_timeseries(
    nii_path: Path,
    atlas_path: Path,
    labels: List[str]
) -> np.ndarray:
    """
    Extract mean time series for each AAL region from fMRI data.

    Args:
        nii_path: Path to preprocessed fMRI NIfTI file.
        atlas_path: Path to AAL atlas NIfTI file.
        labels: List of region labels (for validation).

    Returns:
        Array of shape (n_timepoints, n_regions) containing region-wise time series.
    """
    # Load fMRI data
    fmri_img = nib.load(nii_path)
    fmri_data = fmri_img.get_fdata()
    fmri_shape = fmri_data.shape
    logger.debug(f"Loaded fMRI data with shape: {fmri_shape}")

    # Load atlas
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata()
    atlas_shape = atlas_data.shape
    logger.debug(f"Loaded atlas with shape: {atlas_shape}")

    # Resample atlas to fMRI space if necessary
    if atlas_shape[:3] != fmri_shape[:3]:
        logger.info(f"Resampling atlas from {atlas_shape[:3]} to {fmri_shape[:3]}")
        from nilearn.image import resample_to_img
        atlas_img_resampled = resample_to_img(atlas_img, fmri_img, interpolation='nearest')
        atlas_data = atlas_img_resampled.get_fdata()

    # Flatten spatial dimensions
    n_voxels = fmri_shape[0] * fmri_shape[1] * fmri_shape[2]
    n_timepoints = fmri_shape[3] if len(fmri_shape) == 4 else 1

    # Map each voxel to a region
    # AAL atlas uses integer labels (1-90)
    unique_regions = np.unique(atlas_data)
    # Filter out background (0)
    valid_regions = unique_regions[unique_regions > 0]
    logger.info(f"Found {len(valid_regions)} valid regions in atlas")

    # Initialize timeseries array
    timeseries = np.zeros((n_timepoints, len(valid_regions)))

    # Extract mean time series for each region
    for i, region_idx in enumerate(valid_regions):
        mask = (atlas_data == region_idx)
        # Get voxels belonging to this region
        region_voxels = fmri_data[mask]
        # Reshape to (n_voxels_in_region, n_timepoints) if 4D
        if len(fmri_shape) == 4:
            region_voxels = region_voxels.reshape(-1, n_timepoints)
            # Compute mean across voxels for each timepoint
            timeseries[:, i] = np.mean(region_voxels, axis=0)
        else:
            # 3D case (single timepoint)
            timeseries[0, i] = np.mean(region_voxels)

    # Ensure we have exactly 90 regions
    if timeseries.shape[1] != MATRIX_DIMENSION:
        logger.warning(f"Expected {MATRIX_DIMENSION} regions, got {timeseries.shape[1]}")
        # Pad or truncate
        if timeseries.shape[1] < MATRIX_DIMENSION:
            padding = np.zeros((n_timepoints, MATRIX_DIMENSION - timeseries.shape[1]))
            timeseries = np.hstack([timeseries, padding])
        else:
            timeseries = timeseries[:, :MATRIX_DIMENSION]

    return timeseries

def compute_correlation_matrix(
    timeseries: np.ndarray,
    regularization: float = 1e-6
) -> np.ndarray:
    """
    Compute Pearson correlation matrix from region time series.

    Args:
        timeseries: Array of shape (n_timepoints, n_regions).
        regularization: Small value for numerical stability.

    Returns:
        Correlation matrix of shape (n_regions, n_regions).
    """
    n_timepoints, n_regions = timeseries.shape

    if n_timepoints < 2:
        raise ValueError("Need at least 2 timepoints to compute correlation")

    # Standardize time series (zero mean, unit variance)
    # Handle constant time series
    std = np.std(timeseries, axis=0)
    std[std == 0] = 1.0  # Prevent division by zero
    timeseries_standardized = (timeseries - np.mean(timeseries, axis=0)) / std

    # Compute correlation matrix
    corr_matrix = np.dot(timeseries_standardized.T, timeseries_standardized) / (n_timepoints - 1)

    # Ensure symmetry and numerical stability
    corr_matrix = (corr_matrix + corr_matrix.T) / 2.0
    np.fill_diagonal(corr_matrix, 1.0)  # Ensure diagonal is exactly 1

    # Validate and regularize if necessary
    corr_matrix = validate_and_regularize_matrix(corr_matrix, regularization)

    return corr_matrix

def parcellate_subject(
    subject_id: str,
    fmri_nii_path: Path,
    atlas_path: Optional[Path] = None,
    labels_path: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Process a single subject: extract timeseries and compute connectivity matrix.

    Args:
        subject_id: Subject identifier.
        fmri_nii_path: Path to preprocessed fMRI NIfTI file.
        atlas_path: Path to AAL atlas.
        labels_path: Path to AAL labels.
        output_dir: Directory to save output matrix.

    Returns:
        Path to the saved connectivity matrix.

    Raises:
        FileNotFoundError: If input files don't exist.
        ValueError: If processing fails.
    """
    if output_dir is None:
        output_dir = MATRIX_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    if not fmri_nii_path.exists():
        raise FileNotFoundError(f"fMRI file not found: {fmri_nii_path}")

    if atlas_path is None:
        atlas_path = get_aal_atlas_path()

    if labels_path is None:
        labels_path = DEFAULT_LABELS_PATH

    logger.info(f"Processing subject {subject_id} for parcellation")

    # Load labels
    labels = load_parcellation_labels(labels_path)

    # Extract region timeseries
    timeseries = extract_region_timeseries(fmri_nii_path, atlas_path, labels)
    logger.debug(f"Extracted timeseries with shape: {timeseries.shape}")

    # Compute correlation matrix
    corr_matrix = compute_correlation_matrix(timeseries)
    logger.debug(f"Computed correlation matrix with shape: {corr_matrix.shape}")

    # Save matrix
    output_path = output_dir / f"sub-{subject_id}_matrix.npy"
    np.save(output_path, corr_matrix)
    logger.info(f"Saved connectivity matrix to {output_path}")

    # Save metadata (optional, for debugging)
    metadata_path = output_dir / f"sub-{subject_id}_matrix_meta.json"
    import json
    metadata = {
        "subject_id": subject_id,
        "matrix_shape": corr_matrix.shape,
        "atlas": "AAL",
        "n_regions": MATRIX_DIMENSION,
        "n_timepoints": timeseries.shape[0],
        "has_nan": bool(np.any(np.isnan(corr_matrix))),
        "min_value": float(np.min(corr_matrix)),
        "max_value": float(np.max(corr_matrix)),
        "is_symmetric": bool(np.allclose(corr_matrix, corr_matrix.T)),
        "is_psd": bool(np.all(np.linalg.eigvalsh(corr_matrix) >= -1e-6))
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    return output_path

def run_parcellation_pipeline(
    subject_ids: List[str],
    fmri_base_path: Path,
    atlas_path: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> List[Path]:
    """
    Run parcellation for multiple subjects.

    Args:
        subject_ids: List of subject identifiers.
        fmri_base_path: Base path where fMRI files are located.
        atlas_path: Path to AAL atlas.
        output_dir: Directory to save output matrices.

    Returns:
        List of paths to saved connectivity matrices.
    """
    if output_dir is None:
        output_dir = MATRIX_OUTPUT_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    if atlas_path is None:
        atlas_path = get_aal_atlas_path()

    output_paths = []
    skipped = 0
    failed = 0

    for subject_id in subject_ids:
        # Construct expected fMRI path
        # Expected format: data/processed/preprocessed/sub-<id>_preprocessed.nii.gz
        fmri_path = fmri_base_path / f"sub-{subject_id}_preprocessed.nii.gz"
        if not fmri_path.exists():
            # Try alternative naming
            fmri_path = fmri_base_path / f"sub-{subject_id}.nii.gz"
            if not fmri_path.exists():
                logger.warning(f"fMRI file not found for subject {subject_id}, skipping")
                skipped += 1
                continue

        try:
            output_path = parcellate_subject(
                subject_id=subject_id,
                fmri_nii_path=fmri_path,
                atlas_path=atlas_path,
                output_dir=output_dir
            )
            output_paths.append(output_path)
            logger.info(f"Successfully processed subject {subject_id}")
        except Exception as e:
            logger.error(f"Failed to process subject {subject_id}: {e}")
            failed += 1

    logger.info(f"Parcellation pipeline completed: {len(output_paths)} success, {skipped} skipped, {failed} failed")
    return output_paths

def main():
    """Main entry point for standalone execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Run AAL parcellation pipeline")
    parser.add_argument("--subjects", nargs="+", help="List of subject IDs to process")
    parser.add_argument("--fmri-dir", type=str, default="data/processed", help="Directory containing preprocessed fMRI files")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Directory to save connectivity matrices")
    parser.add_argument("--download-atlas", action="store_true", help="Force download of AAL atlas")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # If no subjects specified, try to find all subjects in the fmri directory
    if not args.subjects:
        fmri_dir = Path(args.fmri_dir)
        if fmri_dir.exists():
            # Look for preprocessed files
            files = list(fmri_dir.glob("sub-*_preprocessed.nii.gz"))
            files += list(fmri_dir.glob("sub-*.nii.gz"))
            subject_ids = list(set([f.stem.replace("_preprocessed", "").replace("sub-", "") for f in files]))
            logger.info(f"Found {len(subject_ids)} subjects to process")
        else:
            logger.error(f"fMRI directory not found: {args.fmri_dir}")
            sys.exit(1)
    else:
        subject_ids = args.subjects

    # Run pipeline
    fmri_path = Path(args.fmri_dir)
    output_path = Path(args.output_dir)

    try:
        run_parcellation_pipeline(
            subject_ids=subject_ids,
            fmri_base_path=fmri_path,
            output_dir=output_path,
            atlas_path=get_aal_atlas_path(force_download=args.download_atlas)
        )
        logger.info("Parcellation pipeline completed successfully")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()