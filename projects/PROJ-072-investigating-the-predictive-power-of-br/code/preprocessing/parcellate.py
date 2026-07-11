"""
Parcellation module for generating connectivity matrices using the AAL atlas.

This module implements AAL atlas parcellation to generate subject-level 
connectivity matrices from preprocessed fMRI data.
"""
import os
import sys
import numpy as np
import nibabel as nib
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
from nilearn import datasets, masking, image
from nilearn.input_data import NiftiLabelsMasker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
AAL_ATLAS_URL = "https://www.gin.cnrs.fr/AAL_files/aal_for_SPM.tar.gz"
DEFAULT_N_ROIS = 90  # Standard AAL atlas has 90 regions
OUTPUT_DIR = Path("data/processed")
METADATA_DIR = Path("data/metadata")
RAW_DIR = Path("data/raw")

def get_aal_atlas_path() -> Path:
    """
    Download or retrieve the AAL atlas files.
    
    Returns:
        Path to the AAL atlas label file and image file.
    """
    # Try to get from nilearn cache first
    try:
        atlas_data = datasets.fetch_atlas_aal()
        atlas_img = Path(atlas_data.maps)
        atlas_labels = Path(atlas_data.labels)
        
        if atlas_img.exists() and atlas_labels.exists():
            logger.info(f"Found AAL atlas in nilearn cache: {atlas_img}")
            return atlas_img, atlas_labels
    except Exception as e:
        logger.warning(f"Could not fetch AAL from nilearn: {e}")
    
    # If not in cache, we'll use nilearn's built-in handling
    # The fetch_atlas_aal will download and cache if needed
    logger.info("Downloading AAL atlas...")
    try:
        atlas_data = datasets.fetch_atlas_aal(download_only=True)
        return Path(atlas_data.maps), Path(atlas_data.labels)
    except Exception as e:
        logger.error(f"Failed to download AAL atlas: {e}")
        raise RuntimeError(f"Could not obtain AAL atlas: {e}")

def load_parcellation_labels(labels_path: Path) -> List[str]:
    """
    Load AAL region labels from file.
    
    Args:
        labels_path: Path to the labels file.
        
    Returns:
        List of region names.
    """
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_path}")
    
    labels = []
    try:
        # AAL labels file format: index, name, x, y, z
        with open(labels_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    # First column is index, second is name
                    labels.append(parts[1])
    except Exception as e:
        logger.error(f"Error reading labels file: {e}")
        raise
    
    logger.info(f"Loaded {len(labels)} region labels")
    return labels

def compute_correlation_matrix(timeseries: np.ndarray) -> np.ndarray:
    """
    Compute Pearson correlation matrix from region timeseries.
    
    Args:
        timeseries: Array of shape (n_timepoints, n_regions).
        
    Returns:
        Correlation matrix of shape (n_regions, n_regions).
    """
    if timeseries.shape[0] < 2:
        raise ValueError("Need at least 2 timepoints to compute correlation")
    
    # Compute correlation matrix
    corr_matrix = np.corrcoef(timeseries, rowvar=False)
    
    # Handle potential NaN values (e.g., constant regions)
    if np.any(np.isnan(corr_matrix)):
        logger.warning("NaN values detected in correlation matrix, replacing with 0")
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    # Ensure diagonal is 1.0
    np.fill_diagonal(corr_matrix, 1.0)
    
    return corr_matrix

def extract_region_timeseries(
    func_img_path: Path, 
    atlas_img_path: Path,
    labels: List[str]
) -> Tuple[np.ndarray, List[str]]:
    """
    Extract mean timeseries for each region from functional image.
    
    Args:
        func_img_path: Path to preprocessed functional image.
        atlas_img_path: Path to AAL atlas image.
        labels: List of region labels.
        
    Returns:
        Tuple of (timeseries array, list of region names).
    """
    if not func_img_path.exists():
        raise FileNotFoundError(f"Functional image not found: {func_img_path}")
    
    if not atlas_img_path.exists():
        raise FileNotFoundError(f"Atlas image not found: {atlas_img_path}")
    
    # Create masker
    masker = NiftiLabelsMasker(
        labels_img=atlas_img_path,
        labels=labels,
        standardize=True,
        detrend=True,
        low_pass=None,  # Assume bandpass already done in preprocessing
        high_pass=None,
        t_r=2.0,  # Default TR, will be read from image if available
        memory="auto",
        verbose=0
    )
    
    try:
        timeseries = masker.fit_transform(func_img_path)
    except Exception as e:
        logger.error(f"Error extracting timeseries: {e}")
        raise
    
    logger.info(f"Extracted timeseries shape: {timeseries.shape}")
    return timeseries, labels

def parcellate_subject(
    subject_id: str,
    preprocessed_img_path: Path,
    atlas_img_path: Path,
    labels: List[str],
    output_dir: Path = OUTPUT_DIR
) -> Path:
    """
    Process a single subject to generate connectivity matrix.
    
    Args:
        subject_id: Subject identifier.
        preprocessed_img_path: Path to preprocessed functional image.
        atlas_img_path: Path to AAL atlas image.
        labels: List of region labels.
        output_dir: Directory to save output.
        
    Returns:
        Path to saved connectivity matrix.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Processing subject: {subject_id}")
    
    # Extract timeseries
    timeseries, region_names = extract_region_timeseries(
        preprocessed_img_path, atlas_img_path, labels
    )
    
    # Compute correlation matrix
    corr_matrix = compute_correlation_matrix(timeseries)
    
    # Save matrix
    matrix_path = output_dir / f"{subject_id}_matrix.npy"
    np.save(matrix_path, corr_matrix)
    
    # Save metadata (region names)
    metadata_path = output_dir / f"{subject_id}_regions.csv"
    pd.DataFrame({'region_name': region_names}).to_csv(metadata_path, index=False)
    
    # Save as CSV as well for easy inspection
    csv_path = output_dir / f"{subject_id}_matrix.csv"
    pd.DataFrame(corr_matrix).to_csv(csv_path, index=False)
    
    logger.info(f"Saved connectivity matrix: {matrix_path}")
    logger.info(f"Matrix shape: {corr_matrix.shape}")
    logger.info(f"Matrix value range: [{corr_matrix.min():.3f}, {corr_matrix.max():.3f}]")
    
    return matrix_path

def run_parcellation_pipeline(
    subjects: Optional[List[str]] = None,
    raw_dir: Path = RAW_DIR,
    atlas_url: str = AAL_ATLAS_URL
) -> Dict[str, Path]:
    """
    Run parcellation pipeline for all subjects.
    
    Args:
        subjects: List of subject IDs to process. If None, processes all found.
        raw_dir: Directory containing raw/preprocessed data.
        atlas_url: URL for AAL atlas.
        
    Returns:
        Dictionary mapping subject_id to output matrix path.
    """
    # Get atlas
    atlas_img_path, labels_path = get_aal_atlas_path()
    labels = load_parcellation_labels(labels_path)
    
    # Find subjects if not provided
    if subjects is None:
        # Look for preprocessed images in data/processed or data/raw
        # Assuming naming convention: sub-<id>_preprocessed.nii.gz
        subjects = []
        for f in raw_dir.glob("sub-*_preprocessed.nii.gz"):
            subject_id = f.stem.replace("_preprocessed", "")
            subjects.append(subject_id)
        logger.info(f"Found {len(subjects)} subjects to process")
    
    results = {}
    for subject_id in subjects:
        # Find preprocessed image
        preprocessed_img = raw_dir / f"{subject_id}_preprocessed.nii.gz"
        if not preprocessed_img.exists():
            logger.warning(f"Preprocessed image not found for {subject_id}, skipping")
            continue
        
        try:
            output_path = parcellate_subject(
                subject_id,
                preprocessed_img,
                atlas_img_path,
                labels
            )
            results[subject_id] = output_path
        except Exception as e:
            logger.error(f"Failed to process subject {subject_id}: {e}")
            continue
    
    logger.info(f"Successfully processed {len(results)} subjects")
    return results

def main():
    """Main entry point for parcellation pipeline."""
    logger.info("Starting AAL parcellation pipeline")
    
    try:
        results = run_parcellation_pipeline()
        
        if not results:
            logger.warning("No subjects were processed successfully")
            return 1
        
        # Log summary
        logger.info("Parcellation completed successfully:")
        for subject_id, path in results.items():
            logger.info(f"  {subject_id}: {path}")
        
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
