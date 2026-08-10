import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Union, Optional

from nilearn.datasets import fetch_atlas_aal

def load_aal_atlas_mask() -> nib.Nifti1Image:
    """
    Fetch and load the AAL atlas mask.
    Returns the Nifti image of the atlas.
    """
    aal_data = fetch_atlas_aal()
    # aal_data.maps is the path to the atlas file
    atlas_img = nib.load(aal_data.maps)
    return atlas_img

def validate_atlas_shape(atlas_img: nib.Nifti1Image, expected_shape: Optional[tuple] = None) -> bool:
    """
    Validate that the atlas image has a valid shape.
    If expected_shape is provided, checks against it.
    """
    shape = atlas_img.shape
    if len(shape) != 3:
        return False
    if expected_shape:
        return shape == expected_shape
    return True

def create_minimal_atlas() -> nib.Nifti1Image:
    """
    Create a minimal dummy atlas for testing if the real one fails.
    This is a fallback ONLY if the real fetch fails, but per constraints
    we should prefer the real fetch. This function creates a 3x3x3 grid.
    """
    data = np.zeros((3, 3, 3), dtype=np.int32)
    # Assign some regions
    data[0, 0, 0] = 1
    data[1, 1, 1] = 2
    data[2, 2, 2] = 3
    
    affine = np.eye(4)
    affine[0, 0] = 2
    affine[1, 1] = 2
    affine[2, 2] = 2
    
    return nib.Nifti1Image(data, affine)
