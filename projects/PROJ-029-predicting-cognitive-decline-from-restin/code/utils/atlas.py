import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Union, Optional

def load_aal_atlas_mask(atlas_path: Union[str, Path]) -> nib.Nifti1Image:
    """Load the AAL atlas image."""
    return nib.load(str(atlas_path))

def validate_atlas_shape(atlas_img: nib.Nifti1Image, expected_shape: tuple) -> bool:
    """Check if atlas shape matches expected."""
    return atlas_img.shape == expected_shape

def create_minimal_atlas(shape: tuple = (91, 109, 91)) -> nib.Nifti1Image:
    """Create a minimal dummy atlas for testing if real one is missing."""
    data = np.zeros(shape, dtype=np.int16)
    # Assign a few ROIs
    data[40:50, 50:60, 40:50] = 1
    data[60:70, 50:60, 40:50] = 2
    affine = np.eye(4)
    affine[0, 0] = 3
    affine[1, 1] = 3
    affine[2, 2] = 3
    return nib.Nifti1Image(data, affine)