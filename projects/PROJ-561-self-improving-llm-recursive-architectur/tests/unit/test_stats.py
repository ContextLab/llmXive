import unittest
import numpy as np
from typing import List, Tuple
from scipy.stats import t

# Import the actual implementation from the project
from pipeline.stats import paired_bootstrap_test, exponential_decay, fit_exponential_decay, detect_plateau_or_degradation

class TestBootstrapSignificance(unittest.TestCase):
    """
    Unit tests for the paired bootstrap significance logic in pipeline.stats.
    Tests verify statistical correctness using known distributions and edge cases.
    """

    def test_bootstrap_significant_difference(self):
        """
        Test that paired_bootstrap_test correctly identifies a significant difference
        when two samples are drawn from distributions with a clear mean difference.
        """
        # Sample A: Mean ~ 0.5
        sample_a = np.random.normal(loc=0.5, scale=0.1, size=1000)
        # Sample B: Mean ~ 0.7 (clearly different)
        sample_b = np.random.normal(loc=0.7, scale=0.1, size=1000)

        # Run bootstrap test
        p_value, mean_diff, ci_lower, ci_upper = paired_bootstrap_test(sample_a, sample_b, n_iterations=1000, alpha=0.05)

        # Assert p-value is small (significant difference)
        self.assertLess(p_value, 0.05, "Expected significant difference between distinct distributions")
        
        # Assert confidence interval does not contain 0
        self.assertNotEqual(0, mean_diff, "Mean difference should not be zero")
        if ci_lower <= ci_upper:
            self.assertTrue(ci_lower > 0 or ci_upper < 0, "CI should not contain 0 for significant difference")

    def test_bootstrap_no_significant_difference(self):
        """
        Test that paired_bootstrap_test correctly identifies NO significant difference
        when two samples are drawn from the same distribution.
        """
        # Both samples from same distribution
        base = np.random.normal(loc=0.5, scale=0.1, size=1000)
        sample_a = base + np.random.normal(0, 0.01, size=1000)
        sample_b = base + np.random.normal(0, 0.01, size=1000)

        # Run bootstrap test
        p_value, mean_diff, ci_lower, ci_upper = paired_bootstrap_test(sample_a, sample_b, n_iterations=1000, alpha=0.05)

        # Assert p-value is large (not significant)
        self.assertGreaterEqual(p_value, 0.05, "Expected no significant difference between identical distributions")

    def test_bootstrap_pairing_structure(self):
        """
        Verify that the paired nature of the test is respected.
        If we swap pairs, the mean difference magnitude should remain consistent
        but sign might flip depending on implementation direction (A-B vs B-A).
        """
        np.random.seed(42)
        sample_a = np.random.normal(0.5, 0.1, 500)
        sample_b = np.random.normal(0.6, 0.1, 500)

        p1, diff1, _, _ = paired_bootstrap_test(sample_a, sample_b, n_iterations=500)
        
        # Reverse order
        p2, diff2, _, _ = paired_bootstrap_test(sample_b, sample_a, n_iterations=500)

        # The magnitude of the difference should be roughly the same
        self.assertAlmostEqual(abs(diff1), abs(diff2), delta=0.05, 
                             msg="Magnitude of mean difference should be symmetric for paired test")

    def test_exponential_decay_function(self):
        """
        Test that the exponential_decay helper function produces expected outputs.
        y = a * exp(-b * x) + c
        """
        x = np.array([0, 1, 2, 3, 4, 5])
        a, b, c = 10.0, 0.5, 2.0
        y = exponential_decay(x, a, b, c)

        # Manual calculation check
        expected_y = a * np.exp(-b * x) + c
        np.testing.assert_array_almost_equal(y, expected_y, decimal=5)

    def test_fit_exponential_decay(self):
        """
        Test that fit_exponential_decay can recover parameters from noiseless data.
        """
        x = np.linspace(0, 10, 50)
        true_a, true_b, true_c = 5.0, 0.3, 1.0
        y = true_a * np.exp(-true_b * x) + true_c

        popt, pcov = fit_exponential_decay(x, y)

        # Recovered parameters should be close to true parameters
        self.assertAlmostEqual(popt[0], true_a, delta=0.5)
        self.assertAlmostEqual(popt[1], true_b, delta=0.1)
        self.assertAlmostEqual(popt[2], true_c, delta=0.5)

    def test_detect_plateau_or_degradation(self):
        """
        Test detection logic for plateau or degradation in a metric trajectory.
        """
        # Case 1: Clear improvement (no plateau/degradation)
        trajectory_improving = [0.1, 0.3, 0.5, 0.7, 0.9]
        plateau_idx, degradation_idx = detect_plateau_or_degradation(trajectory_improving)
        self.assertIsNone(plateau_idx, "No plateau expected in strictly improving sequence")
        self.assertIsNone(degradation_idx, "No degradation expected in strictly improving sequence")

        # Case 2: Degradation
        trajectory_degrading = [0.9, 0.8, 0.7, 0.6, 0.5]
        p_idx, d_idx = detect_plateau_or_degradation(trajectory_degrading)
        # First drop is at index 1 (0.9 -> 0.8)
        self.assertIsNotNone(d_idx, "Degradation expected")
        
        # Case 3: Plateau (flat line)
        trajectory_flat = [0.5, 0.5, 0.5, 0.5]
        p_idx, d_idx = detect_plateau_or_degradation(trajectory_flat)
        self.assertIsNotNone(p_idx, "Plateau expected in flat sequence")

    def test_empty_inputs(self):
        """
        Test that functions handle empty or single-element inputs gracefully (raise errors or return None).
        """
        with self.assertRaises(ValueError):
            paired_bootstrap_test(np.array([]), np.array([]))
        
        with self.assertRaises(ValueError):
            paired_bootstrap_test(np.array([1.0]), np.array([1.0]))

    def test_single_iteration_bootstrap(self):
        """
        Test that the bootstrap test runs with minimal iterations (sanity check).
        """
        sample_a = np.array([1.0, 2.0, 3.0])
        sample_b = np.array([2.0, 3.0, 4.0])
        
        # Should not crash, though statistical validity is low
        p_value, _, _, _ = paired_bootstrap_test(sample_a, sample_b, n_iterations=10)
        self.assertIsInstance(p_value, float)
