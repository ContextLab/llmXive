import unittest
import numpy as np
from typing import List, Tuple
import sys
import os

# Add project root to path if running standalone
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from pipeline.stats import paired_bootstrap_test, exponential_decay, fit_exponential_decay


class TestBootstrapSignificanceLogic(unittest.TestCase):
    """
    Unit tests for bootstrap significance logic in pipeline/stats.py.
    Tests paired_bootstrap_test function for correct p-value calculation
    and statistical validity under known conditions.
    """

    def setUp(self):
        """Set up test fixtures."""
        np.random.seed(42)  # Reproducibility
        self.alpha = 0.05

    def test_identical_distributions_high_pvalue(self):
        """
        When two distributions are identical (or nearly so),
        the bootstrap test should return a high p-value (> alpha).
        """
        # Generate two identical distributions
        baseline = np.random.normal(loc=0.5, scale=0.1, size=1000)
        modified = baseline.copy()  # Exact copy

        p_value = paired_bootstrap_test(baseline, modified, alpha=self.alpha)

        # P-value should be high (fail to reject null hypothesis)
        self.assertGreater(p_value, self.alpha,
                           "Identical distributions should yield high p-value")

    def test_significant_difference_low_pvalue(self):
        """
        When two distributions are significantly different,
        the bootstrap test should return a low p-value (< alpha).
        """
        # Generate two clearly different distributions
        baseline = np.random.normal(loc=0.5, scale=0.05, size=1000)
        modified = np.random.normal(loc=0.7, scale=0.05, size=1000)  # Shifted mean

        p_value = paired_bootstrap_test(baseline, modified, alpha=self.alpha)

        # P-value should be low (reject null hypothesis)
        self.assertLess(p_value, self.alpha,
                        "Significantly different distributions should yield low p-value")

    def test_small_sample_stability(self):
        """
        Test that the bootstrap test handles small sample sizes gracefully
        without crashing, even if statistical power is low.
        """
        baseline = np.array([0.4, 0.5, 0.6, 0.5, 0.45])
        modified = np.array([0.42, 0.48, 0.55, 0.52, 0.47])

        # Should not raise an exception
        p_value = paired_bootstrap_test(baseline, modified, alpha=self.alpha)

        # P-value should be a valid float between 0 and 1
        self.assertIsInstance(p_value, float)
        self.assertGreaterEqual(p_value, 0.0)
        self.assertLessEqual(p_value, 1.0)

    def test_paired_structure_preserved(self):
        """
        Verify that the paired nature of the test is respected.
        When differences are consistently positive, p-value should be low.
        """
        # Create paired data with consistent positive difference
        baseline = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        modified = np.array([1.2, 2.2, 3.2, 4.2, 5.2])  # +0.2 consistently

        p_value = paired_bootstrap_test(baseline, modified, alpha=self.alpha)

        # Should detect the consistent improvement
        self.assertLess(p_value, self.alpha,
                        "Consistently positive differences should yield low p-value")

    def test_asymmetric_distributions(self):
        """
        Test with asymmetric distributions to ensure robustness.
        """
        # Skewed baseline (exponential)
        baseline = np.random.exponential(scale=1.0, size=500) + 0.5
        # Skewed modified (shifted exponential)
        modified = np.random.exponential(scale=1.0, size=500) + 1.0

        p_value = paired_bootstrap_test(baseline, modified, alpha=self.alpha)

        # Should handle non-normal distributions
        self.assertIsInstance(p_value, float)
        self.assertGreaterEqual(p_value, 0.0)
        self.assertLessEqual(p_value, 1.0)

    def test_edge_case_zero_variance(self):
        """
        Test behavior when one distribution has zero variance (constant values).
        """
        baseline = np.ones(100) * 0.5  # Constant
        modified = np.ones(100) * 0.5  # Same constant

        p_value = paired_bootstrap_test(baseline, modified, alpha=self.alpha)

        # Should not crash; p-value should be 1.0 (no difference)
        self.assertEqual(p_value, 1.0,
                         "Identical constant distributions should yield p-value=1.0")

    def test_bootstrap_iterations_parameter(self):
        """
        Verify that the function accepts and uses the n_iterations parameter.
        """
        baseline = np.random.normal(0.5, 0.1, 200)
        modified = np.random.normal(0.6, 0.1, 200)

        # Run with fewer iterations for speed in test
        p_value_fast = paired_bootstrap_test(baseline, modified, n_iterations=100)
        p_value_slow = paired_bootstrap_test(baseline, modified, n_iterations=1000)

        # Both should be valid floats
        self.assertIsInstance(p_value_fast, float)
        self.assertIsInstance(p_value_slow, float)

        # With more iterations, result should be more stable (though not deterministic)
        # Just check that both are in valid range
        self.assertGreaterEqual(p_value_fast, 0.0)
        self.assertLessEqual(p_value_fast, 1.0)
        self.assertGreaterEqual(p_value_slow, 0.0)
        self.assertLessEqual(p_value_slow, 1.0)

    def test_exponential_decay_basic(self):
        """
        Test the exponential_decay function with known parameters.
        """
        x = np.array([0, 1, 2, 3, 4, 5])
        a, b, c = 2.0, 0.5, 1.0
        expected = a * np.exp(-b * x) + c

        result = exponential_decay(x, a, b, c)

        np.testing.assert_array_almost_equal(result, expected, decimal=5,
                                             err_msg="exponential_decay formula incorrect")

    def test_fit_exponential_decay_convergence(self):
        """
        Test that fit_exponential_decay can recover parameters from synthetic data.
        """
        # Generate synthetic data with noise
        true_a, true_b, true_c = 3.0, 0.3, 0.5
        x_data = np.linspace(0, 10, 50)
        y_true = true_a * np.exp(-true_b * x_data) + true_c
        y_noisy = y_true + np.random.normal(0, 0.1, size=x_data.shape)

        # Fit the model
        popt, pcov = fit_exponential_decay(x_data, y_noisy)

        # Recovered parameters should be close to true parameters
        recovered_a, recovered_b, recovered_c = popt

        # Allow reasonable tolerance due to noise
        self.assertAlmostEqual(recovered_a, true_a, delta=0.5,
                               msg=f"a: {recovered_a} vs {true_a}")
        self.assertAlmostEqual(recovered_b, true_b, delta=0.1,
                               msg=f"b: {recovered_b} vs {true_b}")
        self.assertAlmostEqual(recovered_c, true_c, delta=0.2,
                               msg=f"c: {recovered_c} vs {true_c}")


if __name__ == '__main__':
    unittest.main()