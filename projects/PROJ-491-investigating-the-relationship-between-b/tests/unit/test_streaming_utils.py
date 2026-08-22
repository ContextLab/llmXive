"""
Unit tests for streaming_utils.py.

These tests verify the memory-efficient streaming logic without requiring
a full 7GB dataset. They use small synthetic NIfTI files.
"""
import os
import tempfile
import numpy as np
import nibabel as nib
import pytest
from pathlib import Path
import sys
import logging

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from streaming_utils import (
    get_nifti_volume_info,
    verify_memory_constraints,
    stream_nifti_by_time_chunks,
    extract_roi_timeseries_streaming,
    DEFAULT_CHUNK_SIZE
)

# Setup logging for tests
logging.basicConfig(level=logging.INFO)

@pytest.fixture
def small_4d_nifti():
    """Creates a small 4D NIfTI file in a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        shape = (10, 10, 10, 20) # Small volume, 20 timepoints
        data = np.random.rand(*shape).astype(np.float32)
        path = Path(tmpdir) / "test_4d.nii.gz"
        
        # Create NIfTI
        img = nib.Nifti1Image(data, np.eye(4))
        nib.save(img, str(path))
        
        yield str(path), shape, data

@pytest.fixture
def roi_mask():
    """Creates a small 3D ROI mask."""
    with tempfile.TemporaryDirectory() as tmpdir:
        shape = (10, 10, 10)
        mask = np.zeros(shape)
        mask[2:4, 2:4, 2:4] = 1.0 # Small ROI
        path = Path(tmpdir) / "mask.nii.gz"
        
        img = nib.Nifti1Image(mask, np.eye(4))
        nib.save(img, str(path))
        
        yield str(path), mask

def test_get_nifti_volume_info(small_4d_nifti):
    path, expected_shape, _ = small_4d_nifti
    info = get_nifti_volume_info(path)
    
    assert info['shape'] == expected_shape
    assert info['n_volumes'] == 20
    assert info['is_4d'] == True
    assert 'size_bytes' in info
    assert info['voxel_size_bytes'] == 4 # float32

def test_verify_memory_constraints(small_4d_nifti):
    path, _, _ = small_4d_nifti
    # Should pass for small file
    assert verify_memory_constraints(path, chunk_size=5) is True
    
    # Should fail for impossible chunk size (if we force a huge chunk on a small file? No, small file always passes)
    # We can't easily test failure on a small file without changing the logic.
    # But we test that it doesn't raise for valid inputs.

def test_stream_nifti_by_time_chunks(small_4d_nifti):
    path, shape, data = small_4d_nifti
    chunk_size = 5
    
    chunks = list(stream_nifti_by_time_chunks(path, chunk_size=chunk_size))
    
    # Should have 4 chunks (20 / 5)
    assert len(chunks) == 4
    
    for i, (start_idx, chunk) in enumerate(chunks):
        expected_start = i * chunk_size
        assert start_idx == expected_start
        assert chunk.shape[3] == chunk_size
        
        # Verify data integrity
        expected_chunk = data[..., expected_start:expected_start+chunk_size]
        np.testing.assert_array_almost_equal(chunk, expected_chunk)

def test_extract_roi_timeseries_streaming(small_4d_nifti, roi_mask):
    path, shape, data = small_4d_nifti
    mask_path, mask_data = roi_mask
    
    # Calculate expected mean manually
    mask_bool = mask_data > 0.5
    n_voxels = np.sum(mask_bool)
    expected_ts = np.mean(data[mask_bool, :], axis=0)
    
    # Run streaming extraction
    ts = extract_roi_timeseries_streaming(path, mask_path, chunk_size=5)
    
    assert ts.shape == (20,)
    np.testing.assert_array_almost_equal(ts, expected_ts, decimal=5)

def test_streaming_empty_roi(small_4d_nifti):
    with tempfile.TemporaryDirectory() as tmpdir:
        mask_path = Path(tmpdir) / "empty_mask.nii.gz"
        mask_data = np.zeros((10, 10, 10))
        img = nib.Nifti1Image(mask_data, np.eye(4))
        nib.save(img, str(mask_path))
        
        path, _, _ = small_4d_nifti
        
        with pytest.raises(ValueError, match="ROI mask contains no valid voxels"):
            extract_roi_timeseries_streaming(path, str(mask_path))

def test_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        get_nifti_volume_info("/nonexistent/path.nii")

def test_3d_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        shape = (10, 10, 10)
        data = np.random.rand(*shape).astype(np.float32)
        path = Path(tmpdir) / "test_3d.nii.gz"
        
        img = nib.Nifti1Image(data, np.eye(4))
        nib.save(img, str(path))
        
        info = get_nifti_volume_info(str(path))
        assert info['is_4d'] == False
        assert info['n_volumes'] == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])