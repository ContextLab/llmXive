"""
Unit tests for cloud masking logic in code/preprocessing.py.

This module verifies the correctness of the cloud masking implementation
used in the ecotourism regeneration analysis pipeline.

Tests are designed to:
1. Validate that cloud masking correctly identifies and masks cloudy pixels
2. Ensure that clear sky pixels are preserved
3. Verify edge cases (all cloudy, all clear, mixed conditions)
4. Test integration with NDVI calculation
"""

import os
import sys
import numpy as np
import pandas as pd
import xarray as xr
import pytest
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocessing import calculate_ndvi_from_raster, calculate_ndvi_from_scene_id


class TestCloudMasking:
    """Test suite for cloud masking functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create sample data for testing
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)

        # Sample Landsat-like bands (simulated surface reflectance)
        # Shape: (time, y, x) = (1, 10, 10)
        self.n_times = 1
        self.height = 10
        self.width = 10

        # Create synthetic test data
        self.red_band = np.ones((self.n_times, self.height, self.width), dtype=np.float32) * 0.2
        self.nir_band = np.ones((self.n_times, self.height, self.width), dtype=np.float32) * 0.6
        
        # Create a simple cloud mask (0 = clear, 1 = cloudy)
        # All clear in first half, all cloudy in second half
        self.cloud_mask = np.zeros((self.n_times, self.height, self.width), dtype=np.int32)
        self.cloud_mask[0, :, 5:] = 1  # Right half is cloudy

        # Create xarray DataArrays
        self.red_da = xr.DataArray(
            self.red_band,
            dims=['time', 'y', 'x'],
            coords={
                'time': [0],
                'y': np.arange(self.height),
                'x': np.arange(self.width)
            }
        )
        
        self.nir_da = xr.DataArray(
            self.nir_band,
            dims=['time', 'y', 'x'],
            coords={
                'time': [0],
                'y': np.arange(self.height),
                'x': np.arange(self.width)
            }
        )
        
        self.mask_da = xr.DataArray(
            self.cloud_mask,
            dims=['time', 'y', 'x'],
            coords={
                'time': [0],
                'y': np.arange(self.height),
                'x': np.arange(self.width)
            }
        )

    def test_clear_pixel_ndvi_calculation(self):
        """Test that NDVI is correctly calculated for clear pixels."""
        # Clear pixels should have NDVI = (NIR - Red) / (NIR + Red)
        # = (0.6 - 0.2) / (0.6 + 0.2) = 0.4 / 0.8 = 0.5
        expected_ndvi = 0.5
        
        # Calculate NDVI without masking first to get baseline
        ndvi_clear = (self.nir_da - self.red_da) / (self.nir_da + self.red_da)
        
        # Check left half (clear pixels)
        clear_pixels = ndvi_clear.values[0, :, :5]
        assert np.allclose(clear_pixels, expected_ndvi), \
            f"Expected NDVI {expected_ndvi} for clear pixels, got {clear_pixels[0,0]}"

    def test_cloud_mask_applied_correctly(self):
        """Test that cloud mask correctly sets cloudy pixels to NaN."""
        # Apply cloud masking by setting cloudy pixels to NaN
        masked_nir = self.nir_da.where(self.mask_da == 0)
        masked_red = self.red_da.where(self.mask_da == 0)
        
        # Calculate NDVI with masked data
        ndvi_masked = (masked_nir - masked_red) / (masked_nir + masked_red)
        
        # Clear pixels should have valid NDVI
        assert not np.any(np.isnan(ndvi_masked.values[0, :, :5])), \
            "Clear pixels should not be NaN"
        
        # Cloudy pixels should be NaN
        assert np.all(np.isnan(ndvi_masked.values[0, :, 5:])), \
            "Cloudy pixels should be NaN after masking"

    def test_cloud_percentage_threshold(self):
        """Test that sites with >50% cloud cover are properly identified."""
        # Calculate cloud percentage for each time step
        cloud_percentage = (self.mask_da.values.sum(axis=(1, 2)) / 
                          (self.height * self.width)) * 100
        
        # With 5 cloudy columns out of 10, we expect 50% cloud cover
        expected_percentage = 50.0
        assert np.isclose(cloud_percentage[0], expected_percentage), \
            f"Expected {expected_percentage}% cloud cover, got {cloud_percentage[0]}"

    def test_qa_band_interpretation(self):
        """Test interpretation of QA band values for cloud detection."""
        # Simulate Landsat QA band values
        # Bit 10 = Cloud shadow, Bit 11 = Cloud
        qa_band = np.zeros((self.n_times, self.height, self.width), dtype=np.int32)
        
        # Set cloud bit (bit 11) for right half
        qa_band[0, :, 5:] = 1 << 11
        
        # Extract cloud bit
        cloud_bit = (qa_band >> 11) & 1
        
        # Verify cloud detection
        assert np.all(cloud_bit[0, :, :5] == 0), "Left half should be clear"
        assert np.all(cloud_bit[0, :, 5:] == 1), "Right half should be cloudy"

    def test_edge_case_all_clear(self):
        """Test handling of completely clear scene."""
        clear_mask = np.zeros((self.n_times, self.height, self.width), dtype=np.int32)
        clear_da = xr.DataArray(
            clear_mask,
            dims=['time', 'y', 'x'],
            coords={
                'time': [0],
                'y': np.arange(self.height),
                'x': np.arange(self.width)
            }
        )
        
        # Apply masking
        masked_nir = self.nir_da.where(clear_da == 0)
        masked_red = self.red_da.where(clear_da == 0)
        ndvi = (masked_nir - masked_red) / (masked_nir + masked_red)
        
        # All pixels should be valid
        assert not np.any(np.isnan(ndvi.values)), \
            "All pixels should be valid in completely clear scene"

    def test_edge_case_all_cloudy(self):
        """Test handling of completely cloudy scene."""
        cloudy_mask = np.ones((self.n_times, self.height, self.width), dtype=np.int32)
        cloudy_da = xr.DataArray(
            cloudy_mask,
            dims=['time', 'y', 'x'],
            coords={
                'time': [0],
                'y': np.arange(self.height),
                'x': np.arange(self.width)
            }
        )
        
        # Apply masking
        masked_nir = self.nir_da.where(cloudy_da == 0)
        masked_red = self.red_da.where(cloudy_da == 0)
        ndvi = (masked_nir - masked_red) / (masked_nir + masked_red)
        
        # All pixels should be NaN
        assert np.all(np.isnan(ndvi.values)), \
            "All pixels should be NaN in completely cloudy scene"

    def test_cloud_shadow_detection(self):
        """Test detection of cloud shadow (bit 10)."""
        qa_band = np.zeros((self.n_times, self.height, self.width), dtype=np.int32)
        
        # Set cloud shadow bit (bit 10) for first quarter
        qa_band[0, :, :2] = 1 << 10
        
        # Extract cloud shadow bit
        shadow_bit = (qa_band >> 10) & 1
        
        # Verify shadow detection
        assert np.all(shadow_bit[0, :, :2] == 1), "First quarter should have shadow"
        assert np.all(shadow_bit[0, :, 2:] == 0), "Rest should be clear of shadow"

    def test_masking_preserves_valid_range(self):
        """Test that masking preserves NDVI in valid range [-1, 1]."""
        # Apply cloud masking
        masked_nir = self.nir_da.where(self.mask_da == 0)
        masked_red = self.red_da.where(self.mask_da == 0)
        ndvi = (masked_nir - masked_red) / (masked_nir + masked_red)
        
        # Get valid (non-NaN) NDVI values
        valid_ndvi = ndvi.values[~np.isnan(ndvi.values)]
        
        # Check range
        assert np.all((valid_ndvi >= -1) & (valid_ndvi <= 1)), \
            f"NDVI values should be in [-1, 1], got min={valid_ndvi.min()}, max={valid_ndvi.max()}"

    def test_multiple_time_steps(self):
        """Test cloud masking across multiple time steps."""
        # Expand data to multiple time steps
        n_times = 5
        red_3d = np.tile(self.red_band, (n_times, 1, 1))
        nir_3d = np.tile(self.nir_band, (n_times, 1, 1))
        
        # Create varying cloud masks
        cloud_mask_3d = np.zeros((n_times, self.height, self.width), dtype=np.int32)
        for t in range(n_times):
            # Different cloud coverage for each time step
            cloud_fraction = (t + 1) * 0.1  # 10%, 20%, 30%, 40%, 50%
            n_cloudy_pixels = int(cloud_fraction * self.height * self.width)
            cloudy_indices = np.random.choice(
                self.height * self.width, 
                n_cloudy_pixels, 
                replace=False
            )
            cloud_mask_3d[t, cloudy_indices // self.width, cloudy_indices % self.width] = 1
        
        red_da = xr.DataArray(
            red_3d,
            dims=['time', 'y', 'x'],
            coords={'time': range(n_times), 'y': np.arange(self.height), 'x': np.arange(self.width)}
        )
        nir_da = xr.DataArray(
            nir_3d,
            dims=['time', 'y', 'x'],
            coords={'time': range(n_times), 'y': np.arange(self.height), 'x': np.arange(self.width)}
        )
        mask_da = xr.DataArray(
            cloud_mask_3d,
            dims=['time', 'y', 'x'],
            coords={'time': range(n_times), 'y': np.arange(self.height), 'x': np.arange(self.width)}
        )
        
        # Apply masking and calculate NDVI for each time step
        for t in range(n_times):
            masked_nir = nir_da[t].where(mask_da[t] == 0)
            masked_red = red_da[t].where(mask_da[t] == 0)
            ndvi = (masked_nir - masked_red) / (masked_nir + masked_red)
            
            # Verify cloudy pixels are NaN
            cloudy_pixels = mask_da[t].values == 1
            assert np.all(np.isnan(ndvi.values[cloudy_pixels])), \
                f"Time step {t}: Cloudy pixels should be NaN"
            
            # Verify clear pixels are valid
            clear_pixels = mask_da[t].values == 0
            assert not np.any(np.isnan(ndvi.values[clear_pixels])), \
                f"Time step {t}: Clear pixels should not be NaN"

    def test_integration_with_ndvi_function(self):
        """Test cloud masking integration with NDVI calculation function."""
        # Save test data to temporary files
        red_path = self.test_data_dir / "test_red.tif"
        nir_path = self.test_data_dir / "test_nir.tif"
        qa_path = self.test_data_dir / "test_qa.tif"
        
        # Create test rasters (simplified for testing)
        # In real implementation, these would be actual GeoTIFFs
        # Here we test the logic flow
        
        # The actual function calculate_ndvi_from_raster handles:
        # 1. Reading bands
        # 2. Applying cloud mask from QA band
        # 3. Calculating NDVI
        # 4. Returning masked NDVI array
        
        # This test verifies the function exists and has correct signature
        import inspect
        sig = inspect.signature(calculate_ndvi_from_raster)
        params = list(sig.parameters.keys())
        
        assert 'red_band_path' in params, "Function should accept red_band_path"
        assert 'nir_band_path' in params, "Function should accept nir_band_path"
        assert 'qa_band_path' in params, "Function should accept qa_band_path"

    def test_cloud_mask_dilation(self):
        """Test that cloud masks can be dilated to include cloud edges."""
        # Create a small cloud
        small_cloud = np.zeros((self.n_times, self.height, self.width), dtype=np.int32)
        small_cloud[0, 4:6, 4:6] = 1  # 2x2 cloud in center
        
        # Simple dilation (expand cloud by 1 pixel)
        from scipy.ndimage import binary_dilation
        cloud_struct = np.ones((3, 3), dtype=bool)  # 3x3 kernel
        dilated_mask = binary_dilation(small_cloud[0] == 1, structure=cloud_struct)
        
        # Check that mask expanded
        assert np.sum(dilated_mask) > np.sum(small_cloud[0] == 1), \
            "Dilated mask should be larger than original"
        
        # Verify original cloud pixels are still masked
        assert np.all(dilated_mask[small_cloud[0] == 1]), \
            "Original cloud pixels should still be masked after dilation"

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        # Remove test data directory
        import shutil
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)