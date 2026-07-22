import os
import sys
import json
import pytest
import numpy as np
from pathlib import Path
import tempfile
import logging

# Add src to path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from scripts.sweep_thresholds import run_threshold_sweep, load_sample_depth_data
from src.data.pipeline import OccupancyGridConfig, OccupancyGridGenerator

logging.basicConfig(level=logging.WARNING)

class TestThresholdSweep:
    
    def test_load_sample_depth_data_shape(self):
        """Test that the generated depth data has the correct shape."""
        samples = load_sample_depth_data(num_samples=10)
        assert samples.shape[0] == 10
        assert len(samples.shape) == 3  # (N, H, W)
        assert samples.shape[1] == 480  # Height
        assert samples.shape[2] == 640  # Width
        assert np.all(samples >= 0)

    def test_run_threshold_sweep_single_threshold(self):
        """Test running the sweep with a single threshold."""
        depth_data = load_sample_depth_data(num_samples=5)
        thresholds = [1.5]
        
        results = run_threshold_sweep(depth_data, thresholds)
        
        assert "1.5" in results
        assert "mean_occupancy_density" in results["1.5"]
        assert "samples_processed" in results["1.5"]
        assert results["1.5"]["samples_processed"] == 5

    def test_run_threshold_sweep_multiple_thresholds(self):
        """Test running the sweep with multiple thresholds."""
        depth_data = load_sample_depth_data(num_samples=5)
        thresholds = [1.0, 2.0, 3.0]
        
        results = run_threshold_sweep(depth_data, thresholds)
        
        assert len(results) == 3
        for t in thresholds:
            assert str(t) in results
            # Higher threshold should generally result in lower density (fewer occupied cells)
            # This is a heuristic check, not a strict mathematical guarantee due to noise
            # But for a wide enough range, the trend should hold.
            # We just check that the keys exist and have numeric values.
            assert isinstance(results[str(t)]["mean_occupancy_density"], float)

    def test_threshold_impact_on_density(self):
        """
        Verify that changing the threshold actually changes the output density.
        A lower threshold (more sensitive) should yield higher occupancy density
        than a higher threshold (less sensitive), assuming the same data.
        """
        depth_data = load_sample_depth_data(num_samples=20)
        thresholds = [1.0, 3.0]
        
        results = run_threshold_sweep(depth_data, thresholds)
        
        density_low = results["1.0"]["mean_occupancy_density"]
        density_high = results["3.0"]["mean_occupancy_density"]
        
        # With a lower threshold, more pixels are considered "obstacles"
        # So density should be higher for 1.0 than for 3.0
        assert density_low > density_high, \
            f"Expected density at 1.0m ({density_low}) > density at 3.0m ({density_high})"

    def test_empty_data_handling(self):
        """Test behavior with empty depth maps (all zeros)."""
        empty_data = np.zeros((5, 480, 640))
        thresholds = [1.0]
        
        results = run_threshold_sweep(empty_data, thresholds)
        
        # Should handle gracefully, likely resulting in 0 density
        assert results["1.0"]["samples_processed"] == 5
        assert results["1.0"]["mean_occupancy_density"] == 0.0
        
    def test_invalid_threshold_format(self):
        """Test that the script handles invalid input gracefully (via argparse in main, 
        but here we test the core function with bad data if possible, or just structural).
        Since run_threshold_sweep expects valid floats, we test that it processes valid floats correctly."""
        depth_data = load_sample_depth_data(num_samples=2)
        # Test with a very high threshold that might result in empty grids
        results = run_threshold_sweep(depth_data, [100.0])
        assert "100.0" in results
        # Density should be very low or zero
        assert results["100.0"]["mean_occupancy_density"] >= 0
        assert results["100.0"]["mean_occupancy_density"] <= 1.0
