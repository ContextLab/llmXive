import os
import logging
from pathlib import Path
from typing import Union, List, Optional, Tuple
import numpy as np
import nibabel as nib

from config import get_path
from utils.logger import get_logger, ProcessingError
from utils.seed import set_seed

logger = get_logger(__name__)

# Atlas definitions (relative to data/raw or managed by config)
# AAL3 mask is expected to be downloaded to data/raw/AAL3.nii.gz or similar
# Schaefer masks are expected in data/raw/Schaefer2018_*.nii.gz
AAL3_PATH = "data/raw/AAL3.nii.gz"
SCHAEFER_200_PATH = "data/raw/Schaefer2018_400Parcels_7Networks_order_FSLMNI152_2mm.nii.gz"
SCHAEFER_400_PATH = "data/raw/Schaefer2018_400Parcels_7Networks_order_FSLMNI152_2mm.nii.gz"

def load_atlas_mask(atlas_path: Union[str, Path]) -> np.ndarray:
    """
    Load an atlas mask from a NIfTI file and return as a 3D numpy array.
    """
    path = Path(atlas_path)
    if not path.exists():
        raise ProcessingError(f"Atlas mask not found at {path}")
    
    img = nib.load(path)
    data = img.get_fdata().astype(np.int32)
    logger.info(f"Loaded atlas mask from {path}, shape: {data.shape}")
    return data

def load_fMRI_data(fmri_path: Union[str, Path]) -> np.ndarray:
    """
    Load fMRI data from a NIfTI file. Returns a 4D array (x, y, z, time).
    """
    path = Path(fmri_path)
    if not path.exists():
        raise ProcessingError(f"fMRI data not found at {path}")
    
    img = nib.load(path)
    data = img.get_fdata()
    logger.info(f"Loaded fMRI data from {path}, shape: {data.shape}")
    return data

def extract_timeseries_chunked(fmri_data: np.ndarray, atlas_mask: np.ndarray) -> np.ndarray:
    """
    Extract mean time series for each parcel in the atlas mask.
    Uses a chunked approach to handle large 4D arrays efficiently.
    
    Args:
        fmri_data: 4D array (x, y, z, time)
        atlas_mask: 3D array (x, y, z) with integer labels
    
    Returns:
        2D array (num_parcels, time)
    """
    # Flatten spatial dimensions
    mask_flat = atlas_mask.flatten()
    fmri_flat = fmri_data.reshape(-1, fmri_data.shape[-1])
    
    unique_labels = np.unique(mask_flat)
    unique_labels = unique_labels[unique_labels != 0]  # Exclude background
    
    num_parcels = len(unique_labels)
    num_timepoints = fmri_flat.shape[1]
    
    # Pre-allocate output
    timeseries = np.zeros((num_parcels, num_timepoints), dtype=np.float32)
    
    logger.info(f"Extracting timeseries for {num_parcels} parcels...")
    
    for i, label in enumerate(unique_labels):
        # Find voxels belonging to this parcel
        voxel_indices = np.where(mask_flat == label)[0]
        
        # Compute mean across voxels for each timepoint
        parcel_data = fmri_flat[voxel_indices, :]
        timeseries[i, :] = np.mean(parcel_data, axis=0)
    
    return timeseries

def compute_adjacency_matrix(timeseries: np.ndarray) -> np.ndarray:
    """
    Compute the functional connectivity matrix (Pearson correlation)
    from the extracted timeseries.
    
    Args:
        timeseries: 2D array (num_parcels, time)
    
    Returns:
        2D array (num_parcels, num_parcels) correlation matrix
    """
    logger.info(f"Computing adjacency matrix for {timeseries.shape[0]} nodes...")
    
    # Compute correlation matrix
    # np.corrcoef expects (num_variables, num_observations)
    corr_matrix = np.corrcoef(timeseries)
    
    # Handle potential NaNs (e.g., constant time series)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    logger.info(f"Adjacency matrix computed, shape: {corr_matrix.shape}")
    return corr_matrix

def extract_and_parcellate(fmri_path: Union[str, Path], atlas_mask: np.ndarray) -> Tuple[np.ndarray, int]:
    """
    Full pipeline: load fMRI, extract timeseries, compute adjacency matrix.
    
    Args:
        fmri_path: Path to fMRI NIfTI file
        atlas_mask: 3D numpy array of atlas labels
    
    Returns:
        Tuple of (adjacency_matrix, num_nodes)
    """
    fmri_data = load_fMRI_data(fmri_path)
    timeseries = extract_timeseries_chunked(fmri_data, atlas_mask)
    adj_matrix = compute_adjacency_matrix(timeseries)
    return adj_matrix, timeseries.shape[0]

def apply_aal3(subject_id: str, fmri_path: Union[str, Path]) -> str:
    """
    Process a single subject with AAL3 atlas.
    
    Args:
        subject_id: Subject identifier string
        fmri_path: Path to the subject's fMRI data
    
    Returns:
        Path to the output .npz file
    """
    logger.info(f"Applying AAL3 parcellation to subject {subject_id}")
    
    atlas_path = get_path(AAL3_PATH)
    atlas_mask = load_atlas_mask(atlas_path)
    
    adj_matrix, num_nodes = extract_and_parcellate(fmri_path, atlas_mask)
    
    output_path = get_path(f"data/processed/{subject_id}_aal90.npz")
    np.savez_compressed(output_path, adjacency=adj_matrix, num_nodes=num_nodes, atlas="AAL3")
    
    logger.info(f"AAL3 matrix saved to {output_path}")
    return str(output_path)

def apply_schaefer200(subject_id: str, fmri_path: Union[str, Path]) -> str:
    """
    Process a single subject with Schaefer 200-parcel atlas.
    
    Args:
        subject_id: Subject identifier string
        fmri_path: Path to the subject's fMRI data
    
    Returns:
        Path to the output .npz file
    """
    logger.info(f"Applying Schaefer-200 parcellation to subject {subject_id}")
    
    atlas_path = get_path("data/raw/Schaefer2018_200Parcels_7Networks_order_FSLMNI152_2mm.nii.gz")
    atlas_mask = load_atlas_mask(atlas_path)
    
    adj_matrix, num_nodes = extract_and_parcellate(fmri_path, atlas_mask)
    
    output_path = get_path(f"data/processed/{subject_id}_schaefer200.npz")
    np.savez_compressed(output_path, adjacency=adj_matrix, num_nodes=num_nodes, atlas="Schaefer200")
    
    logger.info(f"Schaefer-200 matrix saved to {output_path}")
    return str(output_path)

def apply_schaefer400(subject_id: str, fmri_path: Union[str, Path]) -> str:
    """
    Process a single subject with Schaefer 400-parcel atlas.
    
    This function loads the Schaefer 400-parcel atlas mask, extracts the
    mean time series for each parcel from the fMRI data, computes the
    functional connectivity matrix (Pearson correlation), and saves the
    result to a compressed NumPy archive.
    
    Args:
        subject_id: Subject identifier string (e.g., 'sub-001')
        fmri_path: Path to the subject's fMRI NIfTI data file.
    
    Returns:
        str: Path to the saved output file (data/processed/{subject_id}_schaefer400.npz)
    
    Raises:
        ProcessingError: If the atlas mask is not found or if fMRI data loading fails.
    """
    logger.info(f"Applying Schaefer-400 parcellation to subject {subject_id}")
    
    # Define the path to the Schaefer 400-parcel atlas mask
    # Note: The filename pattern matches the one used in T014 but with 400 parcels
    atlas_filename = "Schaefer2018_400Parcels_7Networks_order_FSLMNI152_2mm.nii.gz"
    atlas_path = get_path(f"data/raw/{atlas_filename}")
    
    # Load the atlas mask
    atlas_mask = load_atlas_mask(atlas_path)
    
    # Extract timeseries and compute adjacency matrix
    adj_matrix, num_nodes = extract_and_parcellate(fmri_path, atlas_mask)
    
    # Define output path
    output_filename = f"{subject_id}_schaefer400.npz"
    output_path = get_path(f"data/processed/{output_filename}")
    
    # Save the result
    np.savez_compressed(
        output_path, 
        adjacency=adj_matrix, 
        num_nodes=num_nodes, 
        atlas="Schaefer400"
    )
    
    logger.info(f"Schaefer-400 matrix saved to {output_path}")
    return str(output_path)

def main():
    """
    Main entry point for running parcellation on a specific subject.
    Usage: python code/parcellate.py --subject <subject_id> --atlas <aal3|schaefer200|schaefer400>
    """
    import argparse
    from utils.logger import log_error_and_raise

    parser = argparse.ArgumentParser(description="Parcellate fMRI data with specified atlas")
    parser.add_argument("--subject", type=str, required=True, help="Subject ID")
    parser.add_argument("--atlas", type=str, required=True, choices=["aal3", "schaefer200", "schaefer400"],
                        help="Atlas to use for parcellation")
    args = parser.parse_args()

    try:
        # Determine fMRI path (assumes standard naming convention)
        fmri_filename = f"sub-{args.subject}_task-rest_bold.nii.gz"
        fmri_path = get_path(f"data/raw/{fmri_filename}")
        
        if not os.path.exists(fmri_path):
            raise ProcessingError(f"fMRI file not found: {fmri_path}")

        if args.atlas == "aal3":
            result = apply_aal3(args.subject, fmri_path)
        elif args.atlas == "schaefer200":
            result = apply_schaefer200(args.subject, fmri_path)
        elif args.atlas == "schaefer400":
            result = apply_schaefer400(args.subject, fmri_path)
        
        print(f"Successfully processed {args.subject} with {args.atlas}. Output: {result}")
    except Exception as e:
        log_error_and_raise(e, ProcessingError, f"Failed to process subject {args.subject}")

if __name__ == "__main__":
    main()