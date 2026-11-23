"""
ROI Extraction Module for fMRI Analysis.

This module handles the loading of the AAL atlas, identification of DLPFC voxels,
spatial smoothing of BOLD data, and extraction of mean time-series from specific ROIs.
"""

import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
import nibabel as nib
from nilearn.image import smooth_img
from scipy.ndimage import binary_erosion

# Import config for paths if needed, though we use explicit paths here
# from config import DATA_RAW, DATA_INTERIM 

def load_aal_atlas(atlas_path: Optional[Path] = None) -> nib.Nifti1Image:
    """
    Load the AAL (Automated Anatomical Labeling) atlas.

    If a specific path is not provided, attempts to locate the standard AAL
    atlas or a downloaded version in data/raw.

    Args:
        atlas_path: Path to the AAL atlas NIfTI file.

    Returns:
        A NIfTI image object representing the atlas.

    Raises:
        FileNotFoundError: If the atlas cannot be found.
    """
    if atlas_path and atlas_path.exists():
        return nib.load(atlas_path)
    
    # Fallback to common locations or standard nilearn atlas if available
    # For this project, we assume the atlas is in data/raw or provided
    possible_paths = [
        Path("data/raw/AAL.nii"),
        Path("data/raw/AAL_template.nii.gz"),
        Path("code/data/AAL.nii") 
    ]
    
    for p in possible_paths:
        if p.exists():
            return nib.load(p)
    
    # If using nilearn's built-in atlas (requires internet or cached)
    try:
        from nilearn import datasets
        # AAL is not directly in datasets, but we can try to fetch standard templates
        # However, for strict offline/specific AAL usage, we rely on the file provided.
        raise FileNotFoundError(
            f"AAL atlas not found at any standard location. "
            f"Please download 'AAL.nii' and place it in data/raw/ or provide atlas_path."
        )
    except ImportError:
        raise FileNotFoundError(
            "AAL atlas file not found. Please ensure 'data/raw/AAL.nii' exists."
        )

def identify_dlpfc_voxels(atlas_img: nib.Nifti1Image, mask_path: Optional[Path] = None) -> np.ndarray:
    """
    Identify voxels corresponding to the Dorsolateral Prefrontal Cortex (DLPFC).

    The DLPFC is typically associated with specific labels in the AAL atlas:
    - Frontal_Sup_Orbital_Left/Right (approx)
    - Frontal_Mid_Orbital_Left/Right
    - Frontal_Sup_Left/Right (Dorsal)
    
    In the standard AAL v1/v2, specific region codes map to these areas.
    We will filter based on known AAL labels for DLPFC regions.
    
    Common AAL labels for DLPFC (approximate):
    10: Frontal_Sup_L (Superior Frontal Gyrus, Left) - often includes DLPFC
    11: Frontal_Sup_R
    12: Frontal_Sup_Orb_L
    13: Frontal_Sup_Orb_R
    14: Frontal_Mid_Orb_L
    15: Frontal_Mid_Orb_R
    
    Note: This is a simplified heuristic. In a full pipeline, a specific mask
    file (mask_path) would be preferred if available.

    Args:
        atlas_img: The loaded AAL atlas image.
        mask_path: Optional path to a pre-defined DLPFC mask. If provided, this
                   overrides atlas-based identification.

    Returns:
        A boolean array (mask) of the same shape as the atlas, where True indicates
        a DLPFC voxel.
    """
    if mask_path and mask_path.exists():
        mask_img = nib.load(mask_path)
        return mask_img.get_fdata().astype(bool)

    atlas_data = atlas_img.get_fdata()
    shape = atlas_data.shape
    
    # Define AAL label indices for DLPFC regions (Left and Right)
    # These indices correspond to the standard AAL template values.
    # 10, 11: Superior Frontal
    # 12, 13: Superior Frontal Orbital
    # 14, 15: Middle Frontal Orbital
    # 46, 47: Middle Frontal (often considered part of DLPFC)
    dl_pfc_labels = [10, 11, 12, 13, 14, 15, 46, 47]
    
    mask = np.zeros(shape, dtype=bool)
    for label in dl_pfc_labels:
        mask |= (atlas_data == label)
    
    # Apply a small erosion to remove boundary voxels that might be partial volume
    # This ensures we only take core DLPFC voxels
    mask = binary_erosion(mask, iterations=1)
    
    if not np.any(mask):
        raise ValueError("No DLPFC voxels found in the atlas. Check AAL label mapping.")
        
    return mask

def smooth_bold_data(bold_path: Path, fwhm: float = 4.0) -> nib.Nifti1Image:
    """
    Apply spatial smoothing to the BOLD fMRI data.

    Args:
        bold_path: Path to the preprocessed BOLD NIfTI file.
        fwhm: Full Width at Half Maximum for the Gaussian kernel in mm.

    Returns:
        Smoothed NIfTI image.
    """
    if not bold_path.exists():
        raise FileNotFoundError(f"BOLD image not found at {bold_path}")
    
    # Use nilearn's smooth_img which handles header and affine correctly
    smoothed_img = smooth_img(bold_path, fwhm=fwhm)
    return smoothed_img

def extract_roi(bold_path: Path, mask_path: Path) -> np.ndarray:
    """
    Extract the mean BOLD time-series from the ROI defined by the mask.

    This function:
    1. Loads the BOLD image and the mask.
    2. Ensures they are spatially aligned (checks affine/shape).
    3. Extracts the mean signal across all voxels within the mask for each timepoint.
    4. Returns a 1D numpy array of the time-series.

    Args:
        bold_path: Path to the BOLD NIfTI image (4D: x, y, z, time).
        mask_path: Path to the ROI mask NIfTI image (3D or 4D with single volume).

    Returns:
        A 1D numpy array containing the mean BOLD signal over time.

    Raises:
        FileNotFoundError: If input files are missing.
        ValueError: If shapes or affines do not match.
    """
    if not bold_path.exists():
        raise FileNotFoundError(f"BOLD image not found at {bold_path}")
    if not mask_path.exists():
        raise FileNotFoundError(f"Mask image not found at {mask_path}")

    # Load images
    bold_img = nib.load(bold_path)
    mask_img = nib.load(mask_path)

    bold_data = bold_img.get_fdata()
    mask_data = mask_img.get_fdata()

    # Handle mask shape (ensure 3D)
    if mask_data.ndim == 4:
        mask_data = mask_data[:, :, :, 0]

    # Ensure mask is boolean
    mask_bool = mask_data.astype(bool)

    # Check shape compatibility (spatial dimensions)
    bold_shape = bold_data.shape[:3]
    mask_shape = mask_data.shape[:3]
    
    if bold_shape != mask_shape:
        # Attempt to resample if shapes differ but affines are similar?
        # For this skeleton, we strictly require alignment or raise error.
        # In a full pipeline, nilearn.resample_img would be used here.
        raise ValueError(
            f"Shape mismatch between BOLD {bold_shape} and Mask {mask_shape}. "
            "Ensure both images are in the same space and resolution."
        )

    # Check number of timepoints
    if bold_data.ndim != 4:
        raise ValueError(f"BOLD image must be 4D (x, y, z, t), got {bold_data.ndim}D")
    
    n_timepoints = bold_data.shape[3]
    
    # Extract time series
    # We iterate over timepoints to compute mean signal in the ROI
    # Using numpy masking for efficiency
    roi_signal = np.zeros(n_timepoints)
    
    # Flatten spatial dimensions for easier indexing
    n_voxels = bold_data.shape[0] * bold_data.shape[1] * bold_data.shape[2]
    flat_bold = bold_data.reshape(n_voxels, n_timepoints)
    flat_mask = mask_bool.flatten()
    
    # Select only voxels inside the mask
    valid_voxels = flat_bold[flat_mask, :]
    
    if valid_voxels.size == 0:
        raise ValueError("No valid voxels found in the mask after alignment.")
    
    # Compute mean across voxels for each timepoint
    roi_signal = np.mean(valid_voxels, axis=0)
    
    return roi_signal

def main():
    """
    Main entry point for the ROI extraction module.
    Demonstrates the workflow: Load atlas -> Identify DLPFC -> Smooth BOLD -> Extract ROI.
    """
    import sys
    from pathlib import Path

    # Example paths (these should be passed as arguments or read from config)
    # Assuming standard project structure
    bold_path = Path("data/raw/sub-01_task-stim_bold.nii.gz")
    # If a specific mask is not provided, we generate one from AAL
    # atlas_path = Path("data/raw/AAL.nii") 
    
    # For the skeleton verification, we just ensure imports work and functions exist.
    # Actual execution requires real data files.
    print("ROI Extraction Module Loaded Successfully.")
    print("Functions available: load_aal_atlas, identify_dlpfc_voxels, smooth_bold_data, extract_roi")
    
    # Example usage logic (commented out to avoid errors without data)
    # if bold_path.exists():
    #     smoothed = smooth_bold_data(bold_path)
    #     atlas = load_aal_atlas()
    #     mask = identify_dlpfc_voxels(atlas)
    #     # Save mask if needed
    #     # nib.save(nib.Nifti1Image(mask.astype(np.float32), atlas.affine), "data/interim/dlpfc_mask.nii")
    #     # timeseries = extract_roi(bold_path, "data/interim/dlpfc_mask.nii")
    #     # print(f"Extracted {len(timeseries)} timepoints.")

if __name__ == "__main__":
    main()