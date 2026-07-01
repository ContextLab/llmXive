"""
Unit tests for code/analysis/avalanches.py
"""
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add code to path if running from tests
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis.avalanches import z_score_normalize, calculate_threshold, detect_avalanches


class TestZScoreNormalize:
    def test_normalization_results_in_zero_mean_unit_std(self):
        """
        Verify that z-score normalization results in a signal with
        mean ~0 and std ~1.
        """
        signal = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        normalized = z_score_normalize(signal)
        
        assert np.isclose(np.mean(normalized), 0.0, atol=1e-5)
        assert np.isclose(np.std(normalized), 1.0, atol=1e-5)

    def test_handles_constant_signal(self):
        """
        Test behavior when input signal is constant (std=0).
        Should avoid division by zero and return zeros or handle gracefully.
        """
        signal = np.array([5.0, 5.0, 5.0, 5.0])
        # The implementation should handle this to avoid runtime errors
        # We expect it to return an array of zeros or similar safe value
        normalized = z_score_normalize(signal)
        
        # If std is 0, mean is 5, (x - mean) / 0 -> inf or nan unless handled.
        # Assuming implementation returns 0s or handles division by zero.
        # We check that it doesn't crash and returns finite values.
        assert np.all(np.isfinite(normalized))


class TestCalculateThreshold:
    def test_threshold_is_percentile_of_signal(self):
        """
        Verify that the calculated threshold corresponds to the requested percentile.
        """
        signal = np.arange(100.0) # 0 to 99
        percentile = 95.0
        
        threshold = calculate_threshold(signal, percentile)
        
        # For 0-99, 95th percentile is roughly 94.5 or 95.0 depending on interpolation
        # We check it's in the expected high range
        assert threshold >= 90.0
        assert threshold <= 99.0

    def test_flat_signal_threshold(self):
        """
        Test threshold calculation on a flat signal (all same value).
        Threshold should be equal to that value.
        """
        signal = np.array([10.0, 10.0, 10.0])
        threshold = calculate_threshold(signal, 90.0)
        assert threshold == pytest.approx(10.0)


class TestDetectAvalanches:
    def test_avalanche_detection_handles_flat_signal(self):
        """
        Test that avalanche detection handles a flat (zero-variance) signal
        without crashing and returns an empty list or valid structure.
        """
        # Flat signal below any reasonable threshold
        flat_signal = np.zeros(100)
        threshold = 0.0
        
        # The function should not raise an exception
        avalanches = detect_avalanches(flat_signal, threshold)
        
        # Should return a list (possibly empty)
        assert isinstance(avalanches, list)

    def test_detects_simple_avalanche(self):
        """
        Test detection on a signal with a clear spike above threshold.
        """
        # Create a signal with a clear 'avalanche' event
        # [0, 0, 2, 2, 2, 0, 0] -> threshold 1.0 -> one avalanche of size 3 (or sum of values)
        signal = np.array([0.0, 0.0, 2.0, 2.0, 2.0, 0.0, 0.0])
        threshold = 1.0
        
        avalanches = detect_avalanches(signal, threshold)
        
        assert isinstance(avalanches, list)
        assert len(avalanches) > 0
        # Check structure of returned avalanche (assuming dict or object with size/start)
        first_avalanche = avalanches[0]
        assert 'size' in first_avalanche or 'start' in first_avalanche or len(first_avalanche) > 0

    def test_no_avalanches_below_threshold(self):
        """
        Test that no avalanches are detected when signal never exceeds threshold.
        """
        signal = np.array([0.5, 0.5, 0.5])
        threshold = 1.0
        
        avalanches = detect_avalanches(signal, threshold)
        assert len(avalanches) == 0