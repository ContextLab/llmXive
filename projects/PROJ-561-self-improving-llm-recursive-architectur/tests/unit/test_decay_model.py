"""
Unit tests for exponential decay model fitting in pipeline.stats.

Tests verify:
1. fit_exponential_decay correctly fits y = a * exp(-b * x) + c
2. The fit parameters are close to known ground truth for synthetic data
3. detect_plateau_or_degradation correctly identifies plateau/degradation points
4. Edge cases: constant data, noisy data, single point
"""

import unittest
import numpy as np
from scipy.optimize import OptimizeResult
from pipeline.stats import fit_exponential_decay, detect_plateau_or_degradation


class TestDecayModelFitting(unittest.TestCase):
    """Tests for exponential decay model fitting functionality."""

    def setUp(self):
        """Set up test fixtures."""
        np.random.seed(42)  # For reproducibility

    def test_fit_exponential_decay_basic(self):
        """Test basic exponential decay fitting with known parameters."""
        # Generate synthetic data with known parameters
        # y = 10 * exp(-0.5 * x) + 2
        x_data = np.linspace(0, 10, 50)
        a_true, b_true, c_true = 10.0, 0.5, 2.0
        y_true = a_true * np.exp(-b_true * x_data) + c_true
        # Add small noise
        y_noisy = y_true + np.random.normal(0, 0.1, size=x_data.shape)

        # Fit the model
        result = fit_exponential_decay(x_data, y_noisy)

        # Check that we got a successful fit
        self.assertIsInstance(result, OptimizeResult)
        self.assertTrue(result.success)

        # Extract fitted parameters
        a_fit, b_fit, c_fit = result.params

        # Check that fitted parameters are close to true values (within 10%)
        self.assertAlmostEqual(a_fit, a_true, delta=a_true * 0.1)
        self.assertAlmostEqual(b_fit, b_true, delta=b_true * 0.1)
        self.assertAlmostEqual(c_fit, c_true, delta=c_true * 0.1)

    def test_fit_exponential_decay_with_noise(self):
        """Test fitting with higher noise levels."""
        x_data = np.linspace(0, 10, 100)
        a_true, b_true, c_true = 5.0, 0.3, 1.0
        y_true = a_true * np.exp(-b_true * x_data) + c_true
        # Add larger noise
        y_noisy = y_true + np.random.normal(0, 0.5, size=x_data.shape)

        result = fit_exponential_decay(x_data, y_noisy)

        self.assertTrue(result.success)
        a_fit, b_fit, c_fit = result.params

        # With larger noise, allow for 20% tolerance
        self.assertAlmostEqual(a_fit, a_true, delta=a_true * 0.2)
        self.assertAlmostEqual(b_fit, b_true, delta=b_true * 0.2)
        self.assertAlmostEqual(c_fit, c_true, delta=c_true * 0.2)

    def test_detect_plateau_or_degradation_plateau(self):
        """Test plateau detection when values stabilize."""
        # Simulate a plateau: values decrease then stabilize
        trajectory = [10.0, 9.0, 8.0, 7.5, 7.2, 7.1, 7.05, 7.02, 7.01, 7.005]
        plateau_idx = detect_plateau_or_degradation(trajectory, threshold=0.05)

        # Should detect plateau around index 5-7 where changes become small
        self.assertIsNotNone(plateau_idx)
        self.assertGreaterEqual(plateau_idx, 4)  # Not too early
        self.assertLessEqual(plateau_idx, 8)  # Not too late

    def test_detect_plateau_or_degradation_degradation(self):
        """Test degradation detection when values start decreasing after improvement."""
        # Simulate degradation: values increase then start decreasing
        trajectory = [10.0, 10.5, 11.0, 11.5, 11.8, 11.6, 11.3, 11.0, 10.5, 10.0]
        degradation_idx = detect_plateau_or_degradation(trajectory, threshold=0.02)

        # Should detect degradation around index 5-6 where values start decreasing
        self.assertIsNotNone(degradation_idx)
        self.assertGreaterEqual(degradation_idx, 4)
        self.assertLessEqual(degradation_idx, 7)

    def test_detect_plateau_or_degradation_no_plateau(self):
        """Test when no plateau or degradation is detected (steady improvement)."""
        # Simulate steady improvement
        trajectory = [10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5]
        result = detect_plateau_or_degradation(trajectory, threshold=0.01)

        # Should return None as no plateau or degradation detected
        self.assertIsNone(result)

    def test_detect_plateau_or_degradation_single_point(self):
        """Test edge case with single data point."""
        trajectory = [10.0]
        result = detect_plateau_or_degradation(trajectory, threshold=0.05)

        # Should return None (not enough points to detect)
        self.assertIsNone(result)

    def test_detect_plateau_or_degradation_two_points(self):
        """Test edge case with two data points."""
        trajectory = [10.0, 10.5]
        result = detect_plateau_or_degradation(trajectory, threshold=0.05)

        # Should return None (not enough points for meaningful detection)
        self.assertIsNone(result)

    def test_fit_exponential_decay_invalid_input(self):
        """Test handling of invalid input (empty arrays)."""
        with self.assertRaises(ValueError):
            fit_exponential_decay(np.array([]), np.array([]))

    def test_fit_exponential_decay_mismatched_lengths(self):
        """Test handling of mismatched array lengths."""
        x_data = np.linspace(0, 10, 10)
        y_data = np.linspace(0, 10, 5)  # Different length

        with self.assertRaises(ValueError):
            fit_exponential_decay(x_data, y_data)

    def test_fit_exponential_decay_constant_data(self):
        """Test fitting with constant data (edge case)."""
        x_data = np.linspace(0, 10, 20)
        y_data = np.ones_like(x_data) * 5.0  # Constant value

        # Should still fit (a=0, c=5)
        result = fit_exponential_decay(x_data, y_data)
        self.assertTrue(result.success)
        a_fit, b_fit, c_fit = result.params
        self.assertAlmostEqual(c_fit, 5.0, delta=0.5)


if __name__ == '__main__':
    unittest.main()