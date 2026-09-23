"""
Unit tests for spatial smoothing functionality.

Tests the core logic of spatial smoothing without requiring real data.
"""

import numpy as np
import pytest
from pathlib import Path
import tempfile
import nibabel as nib

from preprocess.spatial_smoothing import (
    apply_spatial_smoothing,
    compute_pipeline_config_hash,
    process_single_roi_file,
    load_smoothed_timeseries,
    save_smoothed_data
)

class TestComputePipelineConfigHash:
    """Tests for compute_pipeline_config_hash function."""
    
    def test_hash_deterministic(self):
        """Hash should be deterministic for same inputs."""
        hash1 = compute_pipeline_config_hash("test_mask", 4.0, "spatial")
        hash2 = compute_pipeline_config_hash("test_mask", 4.0, "spatial")
        assert hash1 == hash2
        assert len(hash1) == 16
    
    def test_hash_changes_with_kernel(self):
        """Hash should change with different kernel sizes."""
        hash4 = compute_pipeline_config_hash("test_mask", 4.0, "spatial")
        hash8 = compute_pipeline_config_hash("test_mask", 8.0, "spatial")
        assert hash4 != hash8
    
    def test_hash_changes_with_mask(self):
        """Hash should change with different mask names."""
        hash1 = compute_pipeline_config_hash("mask_a", 4.0, "spatial")
        hash2 = compute_pipeline_config_hash("mask_b", 4.0, "spatial")
        assert hash1 != hash2
    
    def test_hash_changes_with_type(self):
        """Hash should change with different smoothing types."""
        hash_spatial = compute_pipeline_config_hash("test_mask", 4.0, "spatial")
        hash_temporal = compute_pipeline_config_hash("test_mask", 4.0, "temporal")
        assert hash_spatial != hash_temporal

class TestApplySpatialSmoothing:
    """Tests for apply_spatial_smoothing function."""
    
    def test_smoothing_reduces_variance(self):
        """Smoothing should reduce variance in noisy data."""
        np.random.seed(42)
        # Create noisy 4D data (x, y, z, t)
        data = np.random.randn(10, 10, 10, 5)
        
        # Apply smoothing
        smoothed = apply_spatial_smoothing(data, kernel_size_mm=4.0)
        
        # Variance should decrease after smoothing
        assert np.var(smoothed) < np.var(data)
    
    def test_smoothing_preserves_shape(self):
        """Smoothed data should have same shape as input."""
        np.random.seed(42)
        data = np.random.randn(10, 10, 10, 5)
        
        smoothed = apply_spatial_smoothing(data, kernel_size_mm=4.0)
        
        assert smoothed.shape == data.shape
    
    def test_larger_kernel_more_smoothing(self):
        """Larger kernel should produce more smoothing."""
        np.random.seed(42)
        data = np.random.randn(10, 10, 10, 5)
        
        smoothed_4mm = apply_spatial_smoothing(data, kernel_size_mm=4.0)
        smoothed_8mm = apply_spatial_smoothing(data, kernel_size_mm=8.0)
        
        # 8mm should be smoother (lower variance) than 4mm
        assert np.var(smoothed_8mm) < np.var(smoothed_4mm)
    
    def test_3d_data_handling(self):
        """Should handle 3D data (x, y, t) correctly."""
        np.random.seed(42)
        data = np.random.randn(10, 10, 5)  # x, y, t
        
        smoothed = apply_spatial_smoothing(data, kernel_size_mm=4.0)
        
        assert smoothed.shape == data.shape
    
    def test_zero_kernel_no_change(self):
        """Zero kernel should not change data (or minimal change due to boundary)."""
        np.random.seed(42)
        data = np.random.randn(10, 10, 10, 5)
        
        smoothed = apply_spatial_smoothing(data, kernel_size_mm=0.0)
        
        # With zero kernel, data should be nearly identical
        np.testing.assert_array_almost_equal(smoothed, data, decimal=5)

class TestLoadSmoothedTimeseries:
    """Tests for load_smoothed_timeseries function."""
    
    def test_load_valid_nifti(self):
        """Should successfully load a valid NIfTI file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            # Create a test NIfTI file
            data = np.random.randn(10, 10, 10, 5)
            img = nib.Nifti1Image(data, np.eye(4))
            test_path = tmpdir / "test.nii.gz"
            nib.save(img, test_path)
            
            # Load it back
            loaded = load_smoothed_timeseries(test_path)
            
            assert loaded.shape == data.shape
            np.testing.assert_array_almost_equal(loaded, data)
    
    def test_load_missing_file_raises(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_smoothed_timeseries(Path("/nonexistent/file.nii.gz"))

class TestSaveSmoothedData:
    """Tests for save_smoothed_data function."""
    
    def test_save_and_reload(self):
        """Saved data should match original after reload."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            # Create reference and data
            data = np.random.randn(10, 10, 10, 5)
            ref_path = tmpdir / "ref.nii.gz"
            out_path = tmpdir / "out.nii.gz"
            
            ref_img = nib.Nifti1Image(data, np.eye(4))
            nib.save(ref_img, ref_path)
            
            # Save smoothed data
            save_smoothed_data(data, out_path, ref_path)
            
            # Reload and verify
            loaded = nib.load(out_path).get_fdata()
            np.testing.assert_array_almost_equal(loaded, data)
    
    def test_creates_output_directory(self):
        """Should create output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            data = np.random.randn(10, 10, 10, 5)
            ref_path = tmpdir / "ref.nii.gz"
            out_path = tmpdir / "subdir" / "out.nii.gz"
            
            ref_img = nib.Nifti1Image(data, np.eye(4))
            nib.save(ref_img, ref_path)
            
            # This should create the subdir
            save_smoothed_data(data, out_path, ref_path)
            
            assert out_path.exists()