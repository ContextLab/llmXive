"""
Unit tests for atlas utilities.
"""
import pytest
import numpy as np
import nibabel as nib
from pathlib import Path
from utils.atlas import load_aal_atlas_mask, validate_atlas_shape

def test_validate_atlas_shape_positive():
    """Test validation with correct shape."""
    data = np.zeros((10, 10, 10))
    img = nib.Nifti1Image(data, np.eye(4))
    assert validate_atlas_shape(img, (10, 10, 10)) is True

def test_validate_atlas_shape_negative():
    """Test validation with incorrect shape."""
    data = np.zeros((10, 10, 10))
    img = nib.Nifti1Image(data, np.eye(4))
    with pytest.raises(ValueError):
        validate_atlas_shape(img, (20, 20, 20))
