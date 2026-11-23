"""
Unit tests for spatial mapping functionality in code/overlap.py.
"""

import numpy as np
import pytest
import tempfile
import nibabel as nib
from pathlib import Path

from overlap import load_atlas_mask, compute_spatial_mapping, generate_mapping_file
from utils.logger import ProcessingError


def create_test_nifti(data: np.ndarray, filename: str) -> Path:
    """Helper to create a temporary NIfTI file."""
    path = Path(filename)
    img = nib.Nifti1Image(data.astype(np.int32), affine=np.eye(4))
    nib.save(img, str(path))
    return path


class TestLoadAtlasMask:
    def test_load_valid_mask(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data = np.zeros((10, 10, 10), dtype=np.int32)
            data[2:4, 2:4, 2:4] = 1
            data[6:8, 6:8, 6:8] = 2
            path = create_test_nifti(data, f"{tmpdir}/test.nii.gz")

            result = load_atlas_mask(path)
            assert result.shape == (10, 10, 10)
            assert result.dtype == np.int32
            assert np.array_equal(result, data)

    def test_load_missing_file(self):
        with pytest.raises(ProcessingError):
            load_atlas_mask("nonexistent.nii.gz")

    def test_load_non_3d(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data = np.zeros((10, 10), dtype=np.int32)
            path = create_test_nifti(data, f"{tmpdir}/test2d.nii.gz")

            with pytest.raises(ProcessingError):
                load_atlas_mask(path)


class TestComputeSpatialMapping:
    def test_simple_majority_vote(self):
        # Create a simple 3x3x3 grid
        # High-res: 2x2x2 block of node 1 in top-left, 1x1x1 node 2 in center
        # Low-res: 1 large region (ID 10) covering the whole thing
        # Expected: Node 1 -> 10, Node 2 -> 10

        shape = (4, 4, 4)
        high_res = np.zeros(shape, dtype=np.int32)
        high_res[0:2, 0:2, 0:2] = 1  # 8 voxels
        high_res[2, 2, 2] = 2         # 1 voxel

        low_res = np.ones(shape, dtype=np.int32) * 10 # All 10

        mapping = compute_spatial_mapping(high_res, low_res)

        assert mapping[1] == 10
        assert mapping[2] == 10
        assert mapping[0] == 0 # Background

    def test_split_vote_majority(self):
        # High-res node 1 occupies 3 voxels in Low-res region A, 1 in B
        # Expected: Node 1 -> A (majority)

        shape = (2, 2, 2)
        high_res = np.ones(shape, dtype=np.int32) # All node 1
        low_res = np.zeros(shape, dtype=np.int32)
        low_res[0, 0, 0] = 10 # 1 voxel
        low_res[0, 0, 1] = 10 # 1 voxel
        low_res[0, 1, 0] = 10 # 1 voxel
        low_res[0, 1, 1] = 20 # 1 voxel
        # Rest 0 (background) - wait, high_res is all 1, so we need low_res to match shape
        # Let's make low_res non-background everywhere high_res is non-background
        low_res[1, :, :] = 20 # 4 voxels
        low_res[0, 1, 1] = 20 # 1 voxel
        # Total for node 1: 3 voxels in 10, 5 voxels in 20?
        # Let's redo simpler:
        # 4 voxels total for node 1.
        # 3 voxels -> region 10
        # 1 voxel -> region 20

        high_res = np.ones((2, 2, 2), dtype=np.int32)
        low_res = np.zeros((2, 2, 2), dtype=np.int32)
        low_res[0, 0, 0] = 10
        low_res[0, 0, 1] = 10
        low_res[0, 1, 0] = 10
        low_res[0, 1, 1] = 20
        # The rest of the 2x2x2 block (indices 1,0,0 etc) are 0 in low_res?
        # If low_res is 0 (background), it counts as a vote for 0?
        # Usually background is ignored or treated as a region.
        # Let's assume background 0 is a valid region for mapping if it has majority.
        # But typically we want to map to non-background.
        # Let's ensure low_res is fully defined.
        low_res[1, :, :] = 10 # Fill the rest with 10

        # Total voxels for node 1: 8
        # Voxels in 10: 3 (top) + 4 (bottom) = 7
        # Voxels in 20: 1
        # Expected: 1 -> 10

        mapping = compute_spatial_mapping(high_res, low_res)
        assert mapping[1] == 10

    def test_shape_mismatch(self):
        high_res = np.zeros((3, 3, 3), dtype=np.int32)
        low_res = np.zeros((4, 4, 4), dtype=np.int32)

        with pytest.raises(ProcessingError):
            compute_spatial_mapping(high_res, low_res)

    def test_background_handling(self):
        # High-res node 1 is entirely in background of low-res (0)
        # Should map to 0
        shape = (4, 4, 4)
        high_res = np.zeros(shape, dtype=np.int32)
        high_res[1:3, 1:3, 1:3] = 1

        low_res = np.zeros(shape, dtype=np.int32) # All background

        mapping = compute_spatial_mapping(high_res, low_res)
        assert mapping[1] == 0

class TestGenerateMappingFile:
    def test_integration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy atlases
            shape = (10, 10, 10)
            high_res_data = np.zeros(shape, dtype=np.int32)
            high_res_data[2:5, 2:5, 2:5] = 1
            high_res_data[6:9, 6:9, 6:9] = 2

            low_res_data = np.ones(shape, dtype=np.int32) * 10
            low_res_data[6:9, 6:9, 6:9] = 20 # Distinct region for node 2

            hr_path = Path(tmpdir) / "hr.nii.gz"
            lr_path = Path(tmpdir) / "lr.nii.gz"
            out_path = Path(tmpdir) / "mapping.npy"

            create_test_nifti(high_res_data, str(hr_path))
            create_test_nifti(low_res_data, str(lr_path))

            result = generate_mapping_file(hr_path, lr_path, out_path)

            assert result.exists()
            mapping = np.load(str(result))

            assert mapping[1] == 10
            assert mapping[2] == 20
            assert mapping[0] == 0
