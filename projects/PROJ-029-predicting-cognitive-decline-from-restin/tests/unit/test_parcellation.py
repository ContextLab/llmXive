"""
Unit tests for AAL atlas parcellation functionality.
Tests atlas loading, validation, and timeseries extraction.
"""
import numpy as np
import nibabel as nib
import pytest
from pathlib import Path
import sys
import tempfile

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from utils.atlas import load_aal_atlas_mask, validate_atlas_shape


class TestAALAtlasLoading:
    """Tests for AAL atlas mask loading and validation."""

    def test_validate_atlas_shape_correct_shape(self):
        """Test validation with correct atlas shape."""
        # Simulate a 90-region atlas (typical AAL)
        # Shape should be (x, y, z) where number of unique labels <= 90
        data = np.zeros((30, 30, 30), dtype=np.int32)
        for i in range(90):
            data[i % 30, i % 30, i % 30] = i + 1

        assert validate_atlas_shape(data) is True

    def test_validate_atlas_shape_too_many_regions(self):
        """Test validation with too many regions."""
        # Create data with 200 unique regions
        data = np.zeros((30, 30, 30), dtype=np.int32)
        for i in range(200):
            data[i % 30, i % 30, i % 30] = i + 1

        # Should return False for > 90 regions
        assert validate_atlas_shape(data) is False

    def test_validate_atlas_shape_empty(self):
        """Test validation with empty atlas."""
        data = np.zeros((30, 30, 30), dtype=np.int32)
        assert validate_atlas_shape(data) is True  # Empty is valid (0 regions)

    def test_validate_atlas_shape_single_region(self):
        """Test validation with single region."""
        data = np.ones((30, 30, 30), dtype=np.int32)
        assert validate_atlas_shape(data) is True

    def test_load_aal_atlas_mask_file_exists(self):
        """Test loading an AAL atlas mask from a temporary file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas_path = Path(tmpdir) / "aal_atlas.nii.gz"
            data = np.zeros((30, 30, 30), dtype=np.int32)
            for i in range(90):
                data[i % 30, i % 30, i % 30] = i + 1

            img = nib.Nifti1Image(data, np.eye(4))
            nib.save(img, str(atlas_path))

            loaded_data, affine = load_aal_atlas_mask(str(atlas_path))

            assert loaded_data.shape == (30, 30, 30)
            assert np.array_equal(affine, np.eye(4))
            assert np.unique(loaded_data).max() == 90

    def test_load_aal_atlas_mask_file_not_found(self):
        """Test loading AAL atlas mask when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_aal_atlas_mask("/nonexistent/path/atlas.nii.gz")

    def test_load_aal_atlas_mask_invalid_extension(self):
        """Test loading AAL atlas mask with invalid file extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas_path = Path(tmpdir) / "atlas.txt"
            atlas_path.write_text("not a nifti file")

            with pytest.raises(Exception):
                load_aal_atlas_mask(str(atlas_path))

    def test_load_aal_atlas_mask_zero_regions(self):
        """Test loading AAL atlas mask with zero regions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas_path = Path(tmpdir) / "empty_atlas.nii.gz"
            data = np.zeros((30, 30, 30), dtype=np.int32)
            img = nib.Nifti1Image(data, np.eye(4))
            nib.save(img, str(atlas_path))

            loaded_data, affine = load_aal_atlas_mask(str(atlas_path))
            assert np.unique(loaded_data).max() == 0
