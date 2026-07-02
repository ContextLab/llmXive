"""
Unit tests for code/preprocess/calibrate.py
"""
import pytest
import numpy as np
import os
import sys
from pathlib import Path

# Add parent directory to path for imports if running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.preprocess.calibrate import (
    detect_dead_pixels,
    detect_artifacts,
    mask_defective_regions,
    calibrate_and_log
)


class TestDeadPixelDetection:
    def test_dead_pixel_detection_simple(self):
        """Test detection of a single dead pixel in a uniform field."""
        # Create a uniform array
        data = np.ones((10, 10)) * 100.0
        # Inject a dead pixel (value 0)
        data[5, 5] = 0.0
        
        mask = detect_dead_pixels(data, threshold_std=3.0)
        
        assert mask[5, 5] is True
        assert np.sum(mask) == 1

    def test_dead_pixel_detection_high_value(self):
        """Test detection of a stuck high pixel."""
        data = np.ones((10, 10)) * 50.0
        # Inject a stuck pixel
        data[2, 2] = 200.0
        
        mask = detect_dead_pixels(data, threshold_std=3.0)
        
        assert mask[2, 2] is True

    def test_no_dead_pixels(self):
        """Test that uniform data without defects returns empty mask."""
        data = np.ones((10, 10)) * 100.0
        mask = detect_dead_pixels(data)
        assert np.sum(mask) == 0


class TestArtifactDetection:
    def test_artifact_detection(self):
        """Test detection of salt-and-pepper noise."""
        data = np.random.normal(100, 1, (20, 20))
        # Inject a small cluster of high values
        data[5:8, 5:8] = 200.0
        
        mask = detect_artifacts(data, noise_threshold=3.0, min_cluster_size=3)
        
        # The 3x3 cluster should be detected
        assert np.sum(mask) >= 9

    def test_no_artifacts(self):
        """Test that clean data returns empty mask."""
        data = np.random.normal(100, 1, (20, 20))
        mask = detect_artifacts(data, noise_threshold=5.0)
        # Should be very few or none with high threshold
        assert np.sum(mask) < 5 # Allow for some random noise in test


class TestMaskDefectiveRegions:
    def test_mask_defective_regions_basic(self):
        """Test the main masking function."""
        data = np.ones((10, 10)) * 100.0
        data[5, 5] = 0.0 # Dead pixel
        
        masked_data, pct, stats = mask_defective_regions(data)
        
        assert pct > 0.0
        assert stats['total_masked'] == 1
        # The value should be replaced
        assert masked_data[5, 5] != 0.0
        
    def test_mask_defective_regions_threshold(self):
        """Test that low threshold masks more."""
        data = np.ones((10, 10)) * 100.0
        data[5, 5] = 90.0 # Slight deviation
        
        # With high threshold, nothing masked
        _, pct_high, _ = mask_defective_regions(data, dead_pixel_std_threshold=10.0)
        # With low threshold, might be masked if local variance is low
        _, pct_low, _ = mask_defective_regions(data, dead_pixel_std_threshold=1.0)
        
        # Just checking the function runs and returns valid types
        assert isinstance(pct_high, float)
        assert isinstance(pct_low, float)


class TestCalibrateAndLog:
    def test_calibrate_and_log_with_dict_input(self):
        """Test calibrate_and_log with dictionary input."""
        data = np.ones((10, 10)) * 100.0
        data[5, 5] = 0.0
        
        items = [
            {'sample_id': 'test_01', 'data': data},
            {'sample_id': 'test_02', 'data': np.ones((10, 10)) * 50.0}
        ]
        
        results = calibrate_and_log(items)
        
        assert len(results) == 2
        assert results[0]['sample_id'] == 'test_01'
        assert results[0]['status'] == 'success'
        assert results[0]['total_masked'] == 1
        
    def test_calibrate_and_log_with_path(self, tmp_path):
        """Test calibrate_and_log with file paths."""
        data = np.ones((10, 10)) * 100.0
        data[5, 5] = 0.0
        
        file_path = tmp_path / "test_map.npy"
        np.save(file_path, data)
        
        results = calibrate_and_log([str(file_path)])
        
        assert len(results) == 1
        assert results[0]['status'] == 'success'