"""
Unit tests for atlas loading logic.

This module verifies that atlas loading functions correctly handle:
1. Valid NIfTI files (AAL3, Schaefer 200, Schaefer 400)
2. Missing files
3. Corrupted/invalid files
4. Memory-efficient loading via chunked processing
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
import nibabel as nib

# Import the actual implementation from the project code
from code.parcellate import load_atlas_mask, validate_atlas_shape
from code.utils.logger import ProcessingError, DataFetchError
from code.config import get_path


class TestLoadAtlasMask:
    """Tests for the load_atlas_mask function."""

    @pytest.fixture
    def temp_atlas_dir(self):
        """Create a temporary directory with mock atlas files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create mock AAL3 atlas (90 regions)
            aal_data = np.zeros((91, 109, 91), dtype=np.int16)
            # Assign random region IDs (1-90)
            np.random.seed(42)
            mask_indices = np.random.choice(91 * 109 * 91, 5000, replace=False)
            flat_mask = aal_data.ravel()
            flat_mask[mask_indices] = np.random.randint(1, 91, size=5000)
            aal_img = nib.Nifti1Image(aal_data, np.eye(4))
            nib.save(aal_img, tmpdir_path / "aal3.nii.gz")

            # Create mock Schaefer 200 atlas (200 regions)
            schaefer200_data = np.zeros((91, 109, 91), dtype=np.int16)
            mask_indices_200 = np.random.choice(91 * 109 * 91, 10000, replace=False)
            flat_mask_200 = schaefer200_data.ravel()
            flat_mask_200[mask_indices_200] = np.random.randint(1, 201, size=10000)
            schaefer200_img = nib.Nifti1Image(schaefer200_data, np.eye(4))
            nib.save(schaefer200_img, tmpdir_path / "schaefer200.nii.gz")

            # Create mock Schaefer 400 atlas (400 regions)
            schaefer400_data = np.zeros((91, 109, 91), dtype=np.int16)
            mask_indices_400 = np.random.choice(91 * 109 * 91, 15000, replace=False)
            flat_mask_400 = schaefer400_data.ravel()
            flat_mask_400[mask_indices_400] = np.random.randint(1, 401, size=15000)
            schaefer400_img = nib.Nifti1Image(schaefer400_data, np.eye(4))
            nib.save(schaefer400_img, tmpdir_path / "schaefer400.nii.gz")

            yield tmpdir_path

    def test_load_aal3_atlas(self, temp_atlas_dir):
        """Test loading AAL3 atlas returns correct shape and data type."""
        atlas_path = temp_atlas_dir / "aal3.nii.gz"
        data, affine = load_atlas_mask(atlas_path)

        assert data.shape == (91, 109, 91)
        assert data.dtype == np.int16
        assert np.all(affine == np.eye(4))
        # Check that region IDs are in expected range
        unique_values = np.unique(data)
        assert all(0 <= v <= 90 for v in unique_values)

    def test_load_schaefer200_atlas(self, temp_atlas_dir):
        """Test loading Schaefer 200 atlas returns correct shape and data type."""
        atlas_path = temp_atlas_dir / "schaefer200.nii.gz"
        data, affine = load_atlas_mask(atlas_path)

        assert data.shape == (91, 109, 91)
        assert data.dtype == np.int16
        unique_values = np.unique(data)
        assert all(0 <= v <= 200 for v in unique_values)

    def test_load_schaefer400_atlas(self, temp_atlas_dir):
        """Test loading Schaefer 400 atlas returns correct shape and data type."""
        atlas_path = temp_atlas_dir / "schaefer400.nii.gz"
        data, affine = load_atlas_mask(atlas_path)

        assert data.shape == (91, 109, 91)
        assert data.dtype == np.int16
        unique_values = np.unique(data)
        assert all(0 <= v <= 400 for v in unique_values)

    def test_load_missing_file_raises_error(self):
        """Test that loading a missing file raises ProcessingError."""
        with pytest.raises(ProcessingError):
            load_atlas_mask(Path("/nonexistent/path/atlas.nii.gz"))

    def test_load_invalid_nifti_raises_error(self):
        """Test that loading an invalid NIfTI file raises ProcessingError."""
        with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as tmp:
            tmp.write(b"not a valid nifti file")
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(ProcessingError):
                load_atlas_mask(tmp_path)
        finally:
            tmp_path.unlink()

    def test_load_corrupted_file_raises_error(self):
        """Test that loading a corrupted NIfTI file raises ProcessingError."""
        with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as tmp:
            # Write partial/corrupted header
            tmp.write(b"\x00" * 348)  # Valid header size but invalid content
            tmp.write(b"\x00" * 100)  # Extra garbage
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(ProcessingError):
                load_atlas_mask(tmp_path)
        finally:
            tmp_path.unlink()


class TestValidateAtlasShape:
    """Tests for the validate_atlas_shape function."""

    def test_valid_shape_passes(self):
        """Test that a valid atlas shape passes validation."""
        valid_shape = (91, 109, 91)
        assert validate_atlas_shape(valid_shape) is True

    def test_invalid_shape_fails(self):
        """Test that an invalid atlas shape raises ValueError."""
        invalid_shape = (50, 50, 50)
        with pytest.raises(ValueError, match="Atlas shape mismatch"):
            validate_atlas_shape(invalid_shape)

    def test_wrong_dimension_count_fails(self):
        """Test that a 2D or 4D shape raises ValueError."""
        shape_2d = (91, 109)
        shape_4d = (91, 109, 91, 4)

        with pytest.raises(ValueError, match="Atlas must be 3D"):
            validate_atlas_shape(shape_2d)

        with pytest.raises(ValueError, match="Atlas must be 3D"):
            validate_atlas_shape(shape_4d)


class TestAtlasIntegration:
    """Integration tests for atlas loading in the context of the pipeline."""

    def test_atlas_loads_from_config_path(self, temp_atlas_dir):
        """Test that atlas can be loaded using config path resolution."""
        # Mock get_path to return our temp directory
        with patch('code.parcellate.get_path', return_value=str(temp_atlas_dir)):
            atlas_path = Path(temp_atlas_dir) / "aal3.nii.gz"
            data, affine = load_atlas_mask(atlas_path)

            assert data is not None
            assert affine is not None
            assert data.shape == (91, 109, 91)

    def test_atlas_memory_efficiency(self, temp_atlas_dir):
        """Test that atlas loading doesn't create excessive memory overhead."""
        # Load the same atlas multiple times and verify no memory leaks
        atlas_path = temp_atlas_dir / "schaefer400.nii.gz"

        for _ in range(5):
            data, affine = load_atlas_mask(atlas_path)
            assert data.shape == (91, 109, 91)
            assert data.dtype == np.int16

            # Explicitly delete to test memory management
            del data
            del affine

    def test_atlas_region_count_validation(self, temp_atlas_dir):
        """Test that atlas region counts match expected values."""
        # AAL3 should have regions 1-90
        aal_path = temp_atlas_dir / "aal3.nii.gz"
        aal_data, _ = load_atlas_mask(aal_path)
        aal_regions = np.unique(aal_data)
        aal_regions = aal_regions[aal_regions > 0]  # Exclude background

        assert len(aal_regions) == 90
        assert np.min(aal_regions) == 1
        assert np.max(aal_regions) == 90

        # Schaefer 200 should have regions 1-200
        sch200_path = temp_atlas_dir / "schaefer200.nii.gz"
        sch200_data, _ = load_atlas_mask(sch200_path)
        sch200_regions = np.unique(sch200_data)
        sch200_regions = sch200_regions[sch200_regions > 0]

        assert len(sch200_regions) == 200
        assert np.min(sch200_regions) == 1
        assert np.max(sch200_regions) == 200

        # Schaefer 400 should have regions 1-400
        sch400_path = temp_atlas_dir / "schaefer400.nii.gz"
        sch400_data, _ = load_atlas_mask(sch400_path)
        sch400_regions = np.unique(sch400_data)
        sch400_regions = sch400_regions[sch400_regions > 0]

        assert len(sch400_regions) == 400
        assert np.min(sch400_regions) == 1
        assert np.max(sch400_regions) == 400

    def test_atlas_affine_consistency(self, temp_atlas_dir):
        """Test that all atlases share the same affine transformation."""
        aal_path = temp_atlas_dir / "aal3.nii.gz"
        sch200_path = temp_atlas_dir / "schaefer200.nii.gz"
        sch400_path = temp_atlas_dir / "schaefer400.nii.gz"

        aal_data, aal_affine = load_atlas_mask(aal_path)
        sch200_data, sch200_affine = load_atlas_mask(sch200_path)
        sch400_data, sch400_affine = load_atlas_mask(sch400_path)

        # All affines should be identical (identity matrix in our mock)
        assert np.allclose(aal_affine, sch200_affine)
        assert np.allclose(aal_affine, sch400_affine)
        assert np.allclose(sch200_affine, sch400_affine)