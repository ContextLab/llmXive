import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Union, Optional
from nilearn.datasets import fetch_atlas_aal

def load_aal_atlas_mask(atlas_path: Optional[Union[str, Path]] = None) -> nib.Nifti1Image:
    """
    Load the AAL atlas mask.
    If atlas_path is provided, load from there. Otherwise, fetch using nilearn.
    """
    if atlas_path is None:
        atlas_data = fetch_atlas_aal()
        atlas_path = atlas_data.maps
    
    return nib.load(str(atlas_path))

def validate_atlas_shape(atlas_img: nib.Nifti1Image, expected_shape: Optional[tuple] = None) -> bool:
    """
    Validate the shape of the atlas image.
    """
    shape = atlas_img.shape
    if expected_shape:
        return shape == expected_shape
    # Basic check: should be 3D
    return len(shape) == 3

def create_minimal_atlas(shape: tuple, n_regions: int = 90) -> nib.Nifti1Image:
    """
    Create a minimal dummy atlas for testing purposes if real atlas is unavailable.
    This should only be used for unit tests, not production.
    """
    data = np.zeros(shape, dtype=np.int16)
    # Fill regions with IDs 1 to n_regions
    # This is a simplified approach for testing
    for i in range(1, n_regions + 1):
        # Place region in a specific voxel (simplified)
        # In a real scenario, we would use proper parcellation
        if i <= shape[0] and i <= shape[1] and i <= shape[2]:
            data[i, i, i] = i
    
    return nib.Nifti1Image(data, np.eye(4))