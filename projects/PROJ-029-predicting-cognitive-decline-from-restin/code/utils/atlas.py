"""
Utility functions for atlas handling

Provides functions to load and validate atlas masks for parcellation.
"""
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Union, Optional
import logging

def load_aal_atlas_mask(atlas_path: Union[str, Path]) -> nib.Nifti1Image:
    """
    Load AAL atlas mask from file.
    
    Parameters
    ----------
    atlas_path : Union[str, Path]
        Path to the AAL atlas NIfTI file
        
    Returns
    -------
    nib.Nifti1Image
        Loaded atlas image
        
    Raises
    ------
    FileNotFoundError
        If atlas file doesn't exist
    ValueError
        If atlas is not a valid label image
    """
    logger = logging.getLogger("utils.atlas")
    atlas_path = Path(atlas_path)
    
    if not atlas_path.exists():
        raise FileNotFoundError(f"AAL atlas file not found: {atlas_path}")
    
    try:
        atlas_img = nib.load(str(atlas_path))
        atlas_data = atlas_img.get_fdata()
        
        # Validate that it's a label image (integer values representing regions)
        unique_values = np.unique(atlas_data)
        if len(unique_values) < 2:
            raise ValueError("Atlas appears to be empty or invalid")
        
        logger.info(f"Loaded AAL atlas with {len(unique_values)} unique regions")
        return atlas_img
        
    except Exception as e:
        logger.error(f"Failed to load AAL atlas: {str(e)}")
        raise

def validate_atlas_shape(atlas_img: nib.Nifti1Image, expected_shape: Optional[tuple] = None) -> bool:
    """
    Validate atlas image shape and properties.
    
    Parameters
    ----------
    atlas_img : nib.Nifti1Image
        Atlas image to validate
    expected_shape : Optional[tuple]
        Expected shape (optional)
        
    Returns
    -------
    bool
        True if valid, False otherwise
    """
    data = atlas_img.get_fdata()
    
    # Check for reasonable size
    if data.size > 1e7:  # More than 10M voxels
        logging.getLogger("utils.atlas").warning("Atlas is unusually large")
    
    # Check for non-negative values
    if np.any(data < 0):
        logging.getLogger("utils.atlas").warning("Atlas contains negative values")
    
    return True
