"""
Unit tests for parcellation and atlas loading.
"""
import pytest
import numpy as np
import nibabel as nib
from pathlib import Path
import tempfile

from utils.atlas import load_aal_atlas_mask, validate_atlas_shape, create_minimal_atlas


class TestAtlasLoading:
    def test_create_minimal_atlas(self):
        """Test creation of a minimal synthetic atlas."""
        shape = (10, 10, 10)
        n_regions = 5
        atlas_img = create_minimal_atlas(shape=shape, n_regions=n_regions)
        
        assert atlas_img is not None
        assert isinstance(atlas_img, nib.Nifti1Image)
        assert atlas_img.shape == shape
        
        data = atlas_img.get_fdata()
        unique_values = np.unique(data)
        # Should have 0 (background) + n_regions
        assert len(unique_values) <= n_regions + 1

    def test_validate_atlas_shape_valid(self):
        """Test validation of a valid atlas shape."""
        shape = (91, 109, 91)
        atlas_img = create_minimal_atlas(shape=shape)
        
        assert validate_atlas_shape(atlas_img) is True

    def test_validate_atlas_shape_invalid_dims(self):
        """Test validation of an atlas with wrong dimensions."""
        # Create a 2D image
        data = np.zeros((10, 10), dtype=np.int32)
        affine = np.eye(4)
        atlas_img = nib.Nifti1Image(data, affine)
        
        assert validate_atlas_shape(atlas_img) is False

    def test_validate_atlas_shape_expected_dims(self):
        """Test validation with expected dimensions."""
        shape = (20, 20, 20)
        atlas_img = create_minimal_atlas(shape=shape)
        
        assert validate_atlas_shape(atlas_img, expected_dims=shape) is True

class TestAtlasMock:
    def test_mock_atlas_loading(self):
        """Test that we can load a mock atlas."""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Create a simple atlas
            shape = (10, 10, 10)
            data = np.random.randint(0, 10, size=shape).astype(np.int32)
            affine = np.eye(4)
            img = nib.Nifti1Image(data, affine)
            nib.save(img, tmp_path)
            
            # Load it back
            loaded_img = nib.load(tmp_path)
            assert loaded_img.shape == shape
        finally:
            import os
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
