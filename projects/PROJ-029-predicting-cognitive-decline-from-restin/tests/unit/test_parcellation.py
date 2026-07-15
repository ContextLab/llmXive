"""
Unit tests for parcellation and atlas utilities.
"""
import pytest
import numpy as np
import nibabel as nib
from pathlib import Path
import tempfile

# Import from project
from utils.atlas import load_aal_atlas_mask, validate_atlas_shape, create_minimal_atlas


class TestAtlasUtils:
    """Tests for atlas utility functions."""

    def test_validate_atlas_shape_valid(self):
        """Test validation with a valid dummy atlas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas_path = Path(tmpdir) / "test_atlas.nii.gz"
            # Create a valid dummy atlas
            create_minimal_atlas(atlas_path, shape=(10, 10, 10), n_regions=5)
            
            assert validate_atlas_shape(atlas_path) is True

    def test_validate_atlas_shape_missing(self):
        """Test validation with a missing file."""
        assert validate_atlas_shape(Path("/nonexistent/file.nii.gz")) is False

    def test_validate_atlas_shape_empty(self):
        """Test validation with an empty (all zeros) atlas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas_path = Path(tmpdir) / "empty_atlas.nii.gz"
            data = np.zeros((10, 10, 10), dtype=np.int16)
            img = nib.Nifti1Image(data, np.eye(4))
            nib.save(img, str(atlas_path))
            
            assert validate_atlas_shape(atlas_path) is False

    def test_load_aal_atlas_mask(self):
        """Test loading an atlas mask."""
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas_path = Path(tmpdir) / "test_atlas.nii.gz"
            create_minimal_atlas(atlas_path, shape=(10, 10, 10), n_regions=5)
            
            data = load_aal_atlas_mask(atlas_path)
            
            assert isinstance(data, np.ndarray)
            assert data.shape == (10, 10, 10)
            assert np.max(data) == 5
            assert np.min(data) == 0

    def test_create_minimal_atlas(self):
        """Test creating a minimal atlas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas_path = Path(tmpdir) / "created_atlas.nii.gz"
            result_path = create_minimal_atlas(atlas_path, shape=(10, 10, 10), n_regions=5)
            
            assert result_path.exists()
            assert result_path == atlas_path
            
            # Verify content
            data = load_aal_atlas_mask(atlas_path)
            assert np.max(data) == 5