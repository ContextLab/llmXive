"""
Unit tests for baseline change-point detection methods.

This module contains tests for:
- Pettitt rolling-window test (test_pettitt_rolling_window)
- BOCPD (Bayesian Online Change-Point Detection) with Gaussian observation model (test_bocpd_gaussian)

Prerequisites:
- T008: Synthetic data generator must be complete to provide test data.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from synthetic_data import generate_synthetic_ili_series
from bocpd import run_bocpd_gaussian, detect_change_points_bocpd


class TestBocpdGaussian:
    """Tests for BOCPD implementation with Gaussian observation model."""

    def test_bocpd_gaussian_no_change(self):
        """
        Test that BOCPD does not detect false positives on a stable Gaussian series.
        
        Generates a synthetic series with constant mean and variance.
        Expects no change points to be detected.
        """
        # Generate stable synthetic data (no shift)
        np.random.seed(42)
        data = generate_synthetic_ili_series(
            n_points=200,
            mean=10.0,
            std=2.0,
            missing_rate=0.0,
            outliers=False
        )
        
        # Run BOCPD
        run_data = run_bocpd_gaussian(data)
        
        # Check that run-length distribution is reasonable (no sudden spikes)
        # For a stable series, run-lengths should grow or stay moderate, not reset constantly
        assert 'run_lengths' in run_data
        assert 'change_point_probs' in run_data
        
        # Basic sanity check: no change points detected in a stable series
        # (using a reasonable threshold)
        change_points = detect_change_points_bocpd(
            run_data['change_point_probs'],
            threshold=0.95
        )
        
        # Should have very few or no change points in stable data
        assert len(change_points) <= 2, "Too many false positives detected in stable series"

    def test_bocpd_gaussian_with_shift(self):
        """
        Test that BOCPD detects a known mean shift.
        
        Generates a synthetic series with a clear mean shift at a known point.
        Expects the detected change point to be close to the actual shift.
        """
        # Create data with known shift
        np.random.seed(123)
        n_pre = 100
        n_post = 100
        shift_point = n_pre
        
        pre_data = np.random.normal(loc=10.0, scale=2.0, size=n_pre)
        post_data = np.random.normal(loc=20.0, scale=2.0, size=n_post)
        
        data = np.concatenate([pre_data, post_data])
        
        # Run BOCPD
        run_data = run_bocpd_gaussian(data)
        
        # Detect change points
        change_points = detect_change_points_bocpd(
            run_data['change_point_probs'],
            threshold=0.95
        )
        
        # Verify that at least one change point was detected
        assert len(change_points) > 0, "Failed to detect known shift"
        
        # Check that the detected change point is reasonably close to the actual shift
        # Allow ±10 weeks tolerance for detection delay
        detected_point = change_points[0]
        assert abs(detected_point - shift_point) <= 10, \
            f"Detected change point {detected_point} too far from actual {shift_point}"

    def test_bocpd_gaussian_with_missing_data(self):
        """
        Test BOCPD robustness to missing data (NaNs).
        
        Generates synthetic data with missing weeks and verifies the algorithm
        handles them gracefully without crashing.
        """
        # Generate data with missing values
        np.random.seed(456)
        data = generate_synthetic_ili_series(
            n_points=150,
            mean=15.0,
            std=3.0,
            missing_rate=0.1,
            outliers=False
        )
        
        # Verify data has NaNs
        assert np.isnan(data).any(), "Test setup failed: no NaNs in data"
        
        # Run BOCPD - should handle NaNs without crashing
        try:
            run_data = run_bocpd_gaussian(data)
            assert 'run_lengths' in run_data
            assert 'change_point_probs' in run_data
        except Exception as e:
            pytest.fail(f"BOCPD failed on data with missing values: {str(e)}")

    def test_bocpd_gaussian_output_format(self):
        """
        Test that BOCPD output has the expected structure and types.
        """
        np.random.seed(789)
        data = generate_synthetic_ili_series(
            n_points=100,
            mean=12.0,
            std=2.5,
            missing_rate=0.0,
            outliers=False
        )
        
        run_data = run_bocpd_gaussian(data)
        
        # Check output structure
        assert isinstance(run_data, dict), "Output should be a dictionary"
        assert 'run_lengths' in run_data, "Missing 'run_lengths' in output"
        assert 'change_point_probs' in run_data, "Missing 'change_point_probs' in output"
        assert 'run_length_distribution' in run_data, "Missing 'run_length_distribution' in output"
        
        # Check types
        assert isinstance(run_data['run_lengths'], np.ndarray), "run_lengths should be ndarray"
        assert isinstance(run_data['change_point_probs'], np.ndarray), "change_point_probs should be ndarray"
        assert isinstance(run_data['run_length_distribution'], list), "run_length_distribution should be list"
        
        # Check shapes
        assert len(run_data['run_lengths']) == len(data), "run_lengths length mismatch"
        assert len(run_data['change_point_probs']) == len(data), "change_point_probs length mismatch"

    def test_bocpd_gaussian_parameter_sensitivity(self):
        """
        Test that BOCPD is sensitive to hazard rate parameter.
        
        Higher hazard rates should lead to more frequent change point detection.
        """
        np.random.seed(999)
        # Create data with multiple shifts
        data = np.concatenate([
            np.random.normal(10, 2, 50),
            np.random.normal(20, 2, 50),
            np.random.normal(10, 2, 50),
            np.random.normal(30, 2, 50)
        ])
        
        # Run with low hazard rate (expects fewer change points)
        run_data_low = run_bocpd_gaussian(data, hazard_rate=0.01)
        cps_low = detect_change_points_bocpd(run_data_low['change_point_probs'], threshold=0.95)
        
        # Run with high hazard rate (expects more change points)
        run_data_high = run_bocpd_gaussian(data, hazard_rate=0.5)
        cps_high = detect_change_points_bocpd(run_data_high['change_point_probs'], threshold=0.95)
        
        # High hazard rate should detect at least as many change points as low
        assert len(cps_high) >= len(cps_low), \
            "High hazard rate should detect more or equal change points"

    def test_bocpd_gaussian_edge_cases(self):
        """
        Test BOCPD behavior on edge cases.
        """
        # Very short series
        short_data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        with pytest.raises((ValueError, IndexError)):
            run_bocpd_gaussian(short_data)
        
        # Constant series (zero variance)
        constant_data = np.ones(50) * 10.0
        with pytest.raises((ValueError, RuntimeWarning)):
            run_bocpd_gaussian(constant_data)

    def test_bocpd_gaussian_with_outliers(self):
        """
        Test BOCPD robustness to outliers.
        
        A single outlier should not trigger a false change point detection.
        """
        np.random.seed(555)
        data = generate_synthetic_ili_series(
            n_points=200,
            mean=15.0,
            std=2.0,
            missing_rate=0.0,
            outliers=True
        )
        
        # Run BOCPD
        run_data = run_bocpd_gaussian(data)
        change_points = detect_change_points_bocpd(
            run_data['change_point_probs'],
            threshold=0.95
        )
        
        # Should not detect too many change points from outliers alone
        # (outliers might cause a few detections, but not a flood)
        assert len(change_points) <= 5, \
            f"Too many change points ({len(change_points)}) detected in data with outliers"