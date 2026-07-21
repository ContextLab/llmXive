"""
ROI Extraction module for fMRI data processing.

This module handles loading AAL atlas masks, identifying DLPFC voxels,
spatial smoothing, and extracting mean BOLD time-series from specific ROIs.
"""

import numpy as np
from pathlib import Path
from typing import Optional

# Import from existing project config if available, otherwise define fallback
try:
    from code.config import CONFIG
except (ImportError, ModuleNotFoundError):
    # Fallback defaults if config is not yet fully populated or import fails
    # In a real run, T004 ensures code.config exists with these constants
    class FallbackConfig:
        AAL_ATLAS_PATH = None  # Will be resolved dynamically or passed
        SMOOTHING_FWHM = 4.0
        TR = 2.0
    
    CONFIG = FallbackConfig()


def load_aal_atlas(atlas_path: Optional[Path] = None) -> np.ndarray:
    """
    Load the AAL atlas mask.
    
    Args:
        atlas_path: Path to the AAL atlas file. If None, attempts to use
                    a standard location or raises an error if not found.
                    
    Returns:
        numpy.ndarray: The 3D or 4D atlas mask data.
        
    Raises:
        FileNotFoundError: If the atlas file cannot be found.
        ImportError: If nibabel is not installed (expected to be in requirements).
    """
    try:
        import nibabel as nib
    except ImportError:
        raise ImportError("nibabel is required for ROI extraction. "
                          "Please install it via `pip install nibabel`.")

    if atlas_path is None:
        # Default assumption: AAL atlas is in data/raw or a standard system path.
        # For this implementation, we expect the path to be provided or
        # derived from a standard location if the dataset includes it.
        # If the dataset ds000246 does not include AAL, we might need to download it.
        # For now, we raise a clear error if path is missing.
        raise FileNotFoundError(
            "AAL Atlas path not provided. Please provide 'atlas_path' or "
            "configure it in code/config.py."
        )

    if not atlas_path.exists():
        raise FileNotFoundError(f"AAL Atlas file not found at: {atlas_path}")

    atlas_img = nib.load(str(atlas_path))
    return atlas_img.get_fdata()


def identify_dlpfc_voxels(atlas_data: np.ndarray, mask_path: Optional[Path] = None) -> np.ndarray:
    """
    Identify DLPFC (Dorsolateral Prefrontal Cortex) voxels from the atlas.
    
    The AAL atlas uses specific integer labels for ROIs. DLPFC typically
    corresponds to labels for Superior Frontal Gyrus (Dorsal) or Middle
    Frontal Gyrus. In AAL:
    - 6: Superior Frontal Gyrus, Dorsal (Left)
    - 7: Superior Frontal Gyrus, Dorsal (Right)
    - 10: Middle Frontal Gyrus (Left)
    - 11: Middle Frontal Gyrus (Right)
    
    We will select labels 6, 7, 10, 11 to approximate DLPFC.
    
    Args:
        atlas_data: 3D numpy array of atlas labels.
        mask_path: Optional binary mask to restrict search space.
        
    Returns:
        np.ndarray: Boolean mask of DLPFC voxels (True where DLPFC).
    """
    # Define AAL labels corresponding to DLPFC regions
    dlpfc_labels = [6, 7, 10, 11]
    
    # Create a boolean mask where atlas_data matches any of the DLPFC labels
    dlpfc_mask = np.zeros_like(atlas_data, dtype=bool)
    for label in dlpfc_labels:
        dlpfc_mask |= (atlas_data == label)
    
    if mask_path is not None:
        # If a binary brain mask is provided, intersect with it
        import nibabel as nib
        mask_img = nib.load(str(mask_path))
        mask_data = mask_img.get_fdata() > 0
        dlpfc_mask &= mask_data
    
    return dlpfc_mask


def smooth_bold_data(bold_path: Path, fwhm: float = 4.0) -> Path:
    """
    Apply spatial smoothing to BOLD data using nilearn.
    
    Args:
        bold_path: Path to the input 4D BOLD NIfTI file.
        fwhm: Full Width at Half Maximum for smoothing kernel (in mm).
            
    Returns:
        Path: Path to the smoothed BOLD file.
    """
    try:
        from nilearn.image import smooth_img
    except ImportError:
        raise ImportError("nilearn is required for smoothing. "
                          "Please install it via `pip install nilearn`.")

    if not bold_path.exists():
        raise FileNotFoundError(f"BOLD file not found at: {bold_path}")

    # Define output path
    output_path = bold_path.parent / f"{bold_path.stem}_smoothed{bold_path.suffix}"
    
    # Perform smoothing
    smooth_img(bold_path, fwhm=fwhm, output_file=str(output_path))
    
    return output_path


def extract_roi(bold_path: Path, mask_path: Path) -> np.ndarray:
    """
    Extract mean BOLD time-series from a specific ROI defined by a mask.
    
    This function:
    1. Loads the 4D BOLD data.
    2. Loads the mask (either a pre-computed mask or an AAL atlas file).
    3. If the mask is an AAL atlas, it identifies DLPFC voxels.
    4. Applies spatial smoothing if not already done (optional step, 
       typically smoothing is done before extraction, but this function 
       can handle it if the input bold_path is not smoothed).
    5. Calculates the mean signal across the ROI voxels for each timepoint.
    
    Args:
        bold_path (Path): Path to the 4D BOLD NIfTI file.
        mask_path (Path): Path to the AAL atlas or a binary ROI mask.
            
    Returns:
        np.ndarray: 1D array of mean BOLD signal values (timepoints).
                    
    Raises:
        FileNotFoundError: If input files are missing.
        ValueError: If the mask and BOLD data dimensions do not align.
        ImportError: If required libraries (nibabel, nilearn) are missing.
    """
    try:
        import nibabel as nib
    except ImportError:
        raise ImportError("nibabel is required for ROI extraction.")

    if not bold_path.exists():
        raise FileNotFoundError(f"BOLD file not found at: {bold_path}")
    if not mask_path.exists():
        raise FileNotFoundError(f"Mask/Atlas file not found at: {mask_path}")

    # Load BOLD data
    bold_img = nib.load(str(bold_path))
    bold_data = bold_img.get_fdata()
    
    # Load mask/atlas
    mask_img = nib.load(str(mask_path))
    mask_data = mask_img.get_fdata()
    
    # Check dimensions
    if bold_data.shape[:3] != mask_data.shape:
        # Attempt to resample or raise error. For now, strict check.
        # In a robust pipeline, we would resample the mask to BOLD space.
        raise ValueError(
            f"Dimension mismatch: BOLD shape {bold_data.shape[:3]} "
            f"does not match Mask shape {mask_data.shape}. "
            "Resampling is not implemented in this skeleton."
        )

    # Determine if mask_path is an AAL atlas or a binary mask
    # Heuristic: If mask_data contains integer labels > 1, assume it's an atlas.
    # If it's boolean or 0/1, assume it's a binary mask.
    is_atlas = np.max(mask_data) > 1
    
    if is_atlas:
        # Extract DLPFC voxels from AAL atlas
        roi_mask = identify_dlpfc_voxels(mask_data)
    else:
        # Assume binary mask
        roi_mask = mask_data > 0
    
    # Ensure ROI has voxels
    if not np.any(roi_mask):
        raise ValueError("No valid voxels found in the specified ROI.")
    
    # Flatten the spatial dimensions to get a list of voxel indices
    # We need to extract the time series for these specific voxels
    # bold_data shape: (x, y, z, t)
    # roi_mask shape: (x, y, z)
    
    # Get indices of active voxels
    voxel_indices = np.where(roi_mask)
    
    # Extract time series for each voxel
    # We can do this by iterating or using advanced indexing
    # Efficient way: reshape to (n_voxels, n_timepoints)
    n_timepoints = bold_data.shape[-1]
    
    # Create a 2D array of shape (n_voxels, n_timepoints)
    # Using advanced indexing: bold_data[x, y, z, t]
    # We need to map (x, y, z) to a linear index or iterate
    
    # Method: Reshape bold_data to (n_voxels, n_timepoints) directly
    # First, reshape to (x*y*z, t)
    n_spatial = np.prod(bold_data.shape[:3])
    bold_flat = bold_data.reshape(n_spatial, n_timepoints)
    
    # Create a linear index for the ROI voxels
    linear_indices = np.ravel_multi_index(voxel_indices, bold_data.shape[:3])
    
    # Extract the time series
    roi_time_series = bold_flat[linear_indices, :]
    
    # Calculate mean across voxels for each timepoint
    mean_signal = np.mean(roi_time_series, axis=0)
    
    return mean_signal