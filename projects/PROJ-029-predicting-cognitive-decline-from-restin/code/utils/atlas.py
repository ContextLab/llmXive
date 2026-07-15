"""
Atlas utilities for loading and validating AAL atlas masks.
"""
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Union, Optional

import logging

logger = logging.getLogger(__name__)


def load_aal_atlas_mask(
    atlas_path: Optional[Union[str, Path]] = None
) -> nib.Nifti1Image:
    """
    Load the AAL atlas mask.
    
    If atlas_path is not provided, attempts to fetch from nilearn.
    
    Returns:
        nib.Nifti1Image: The loaded atlas mask.
    """
    if atlas_path is None:
        try:
            from nilearn.datasets import fetch_atlas_aal
            atlas_data = fetch_atlas_aal()
            atlas_path = atlas_data.maps
        except Exception as e:
            raise RuntimeError(f"Failed to fetch AAL atlas: {e}")
    
    if isinstance(atlas_path, str):
        atlas_path = Path(atlas_path)
    
    if not atlas_path.exists():
        raise FileNotFoundError(f"AAL atlas file not found: {atlas_path}")
    
    mask_img = nib.load(str(atlas_path))
    logger.info(f"Loaded AAL atlas from {atlas_path}")
    return mask_img


def validate_atlas_shape(
    atlas_img: nib.Nifti1Image,
    expected_dims: Optional[tuple] = None
) -> bool:
    """
    Validate that the atlas has reasonable dimensions.
    
    Args:
        atlas_img: The atlas image to validate.
        expected_dims: Optional tuple of expected dimensions (x, y, z).
        
    Returns:
        bool: True if valid, False otherwise.
    """
    shape = atlas_img.shape
    logger.debug(f"Atlas shape: {shape}")
    
    if len(shape) != 3:
        logger.warning(f"Atlas should be 3D, got {len(shape)}D")
        return False
    
    if expected_dims:
        if shape != expected_dims:
            logger.warning(f"Atlas shape {shape} does not match expected {expected_dims}")
            # We don't fail strictly, just warn
    
    return True


def create_minimal_atlas(
    shape: tuple = (91, 109, 91),
    n_regions: int = 116
) -> nib.Nifti1Image:
    """
    Create a minimal synthetic atlas for testing.
    
    Args:
        shape: The shape of the atlas volume.
        n_regions: Number of regions to create.
        
    Returns:
        nib.Nifti1Image: A synthetic atlas mask.
    """
    data = np.zeros(shape, dtype=np.int32)
    
    # Assign region IDs
    voxels = np.arange(n_regions) + 1
    for i, idx in enumerate(np.random.choice(np.prod(shape), n_regions, replace=False)):
        data.flat[idx] = voxels[i]
    
    # Create affine (identity for simplicity)
    affine = np.eye(4)
    
    return nib.Nifti1Image(data, affine)
