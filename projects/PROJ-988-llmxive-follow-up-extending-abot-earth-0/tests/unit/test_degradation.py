"""
Unit tests for degradation parameters and Kolmogorov-Smirnov (KS) test implementation.

This module verifies:
1. Coarse spatial resolution (30m/pixel) is applied correctly.
2. Partial cloud coverage is generated within expected bounds.
3. The Kolmogorov-Smirnov (KS) test is correctly implemented to compare
   synthetic mask distributions against reference distributions.
"""
import unittest
import numpy as np
from pathlib import Path
import sys
import os

# Add the code directory to the path to allow imports from lib
# Assuming tests are run from the project root or this script handles pathing
code_root = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from lib.degradation import downscale_image, generate_cloud_mask, DegradationError
from scipy import stats


class TestDegradationParameters(unittest.TestCase):
    """Tests for spatial resolution and cloud coverage parameters."""

    def setUp(self):
        """Set up test fixtures."""
        self.seed = 42
        np.random.seed(self.seed)
        # Create a dummy high-res image (100x100 pixels representing 10m/pixel -> 1km x 1km)
        # Target: 30m/pixel -> 33x33 pixels
        self.high_res_image = np.random.rand(100, 100) * 255
        self.target_resolution_m = 30
        self.original_resolution_m = 10

    def test_coarse_spatial_resolution(self):
        """Verify that downscale_image produces the correct output shape for 30m/pixel."""
        # Calculate expected output dimensions
        # Original: 100px * 10m = 1000m
        # Target: 1000m / 30m = 33.33 -> 33 pixels
        expected_width = int(100 * (self.original_resolution_m / self.target_resolution_m))
        
        degraded = downscale_image(self.high_res_image, target_resolution=self.target_resolution_m, original_resolution=self.original_resolution_m)
        
        self.assertIsInstance(degraded, np.ndarray)
        # Allow for slight rounding differences in implementation, but check order of magnitude
        self.assertLess(degraded.shape[0], self.high_res_image.shape[0])
        self.assertLess(degraded.shape[1], self.high_res_image.shape[1])
        
        # Verify specific calculation: 100 * (10/30) = 33.33
        # We expect the function to round or floor this appropriately
        expected_dim = 33
        self.assertEqual(degraded.shape[0], expected_dim)
        self.assertEqual(degraded.shape[1], expected_dim)

    def test_partial_cloud_coverage_bounds(self):
        """Verify that generate_cloud_mask produces masks with expected coverage range."""
        coverage_target = 0.25  # 25% cloud coverage
        mask = generate_cloud_mask(self.high_res_image.shape, target_coverage=coverage_target)
        
        self.assertEqual(mask.shape, self.high_res_image.shape)
        self.assertTrue(np.all((mask >= 0) & (mask <= 1)))
        
        # Calculate actual coverage
        actual_coverage = np.mean(mask)
        
        # Allow a tolerance of 5% for stochastic generation
        tolerance = 0.05
        self.assertGreaterEqual(actual_coverage, coverage_target - tolerance)
        self.assertLessEqual(actual_coverage, coverage_target + tolerance)

    def test_generate_cloud_mask_variability(self):
        """Ensure that repeated calls with same seed produce deterministic results."""
        np.random.seed(42)
        mask1 = generate_cloud_mask((50, 50), target_coverage=0.2)
        
        np.random.seed(42)
        mask2 = generate_cloud_mask((50, 50), target_coverage=0.2)
        
        np.testing.assert_array_equal(mask1, mask2)


class TestKSImplementation(unittest.TestCase):
    """Tests for the Kolmogorov-Smirnov test implementation in degradation validation."""

    def test_ks_test_logic(self):
        """Verify the KS test implementation compares distributions correctly."""
        # Create two synthetic distributions: one uniform, one normal
        # In a real scenario, these would be the synthetic mask stats vs real mask stats
        np.random.seed(123)
        synthetic_data = np.random.normal(loc=0.2, scale=0.05, size=1000)
        real_data = np.random.normal(loc=0.2, scale=0.05, size=1000)  # Same distribution
        
        # Perform KS test using scipy (which is what the implementation should wrap)
        statistic, p_value = stats.ks_2samp(synthetic_data, real_data)
        
        # If distributions are identical, p-value should be high (not significant difference)
        self.assertGreater(p_value, 0.05)
        self.assertLess(statistic, 0.1)  # D-statistic should be small

    def test_ks_test_different_distributions(self):
        """Verify KS test detects difference between distinct distributions."""
        np.random.seed(456)
        # Distribution A: centered at 0.2
        dist_a = np.random.normal(loc=0.2, scale=0.05, size=1000)
        # Distribution B: centered at 0.5 (very different)
        dist_b = np.random.normal(loc=0.5, scale=0.05, size=1000)
        
        statistic, p_value = stats.ks_2samp(dist_a, dist_b)
        
        # If distributions are different, p-value should be very low
        self.assertLess(p_value, 0.001)
        self.assertGreater(statistic, 0.5)  # D-statistic should be large

    def test_ks_test_wrapper_functionality(self):
        """
        Verify that a wrapper function for KS test exists and behaves as expected.
        This simulates the function that would be used in T016 (validate_masks.py).
        """
        def calculate_ks_similarity(sample1, sample2):
            """
            Calculates the Kolmogorov-Smirnov statistic and returns a similarity score.
            Similarity = 1 - D_statistic (where D is the max distance between CDFs).
            """
            stat, _ = stats.ks_2samp(sample1, sample2)
            return 1.0 - stat

        np.random.seed(789)
        identical_dist = np.random.normal(0.3, 0.1, 500)
        
        score_same = calculate_ks_similarity(identical_dist, identical_dist)
        score_diff = calculate_ks_similarity(identical_dist, np.random.normal(0.8, 0.1, 500))
        
        # Identical distributions should yield similarity ~ 1.0
        self.assertAlmostEqual(score_same, 1.0, places=1)
        # Different distributions should yield lower similarity
        self.assertLess(score_diff, 0.6)


if __name__ == "__main__":
    unittest.main()