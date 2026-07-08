"""
Unit tests for JS divergence calculation (base=2).
Tests for src/models/metrics/divergence.py
"""
import unittest
import numpy as np
from scipy.special import kl_div
from src.models.metrics.divergence import compute_js_divergence, validate_probability_vector


class TestJSdivergenceCalculation(unittest.TestCase):
    """Tests for Jensen-Shannon divergence calculation with base 2."""

    def setUp(self):
        """Set up test fixtures."""
        self.seed = 42
        np.random.seed(self.seed)

    def test_identical_distributions_zero_divergence(self):
        """JS divergence should be 0 for identical distributions."""
        p = np.array([0.5, 0.3, 0.2])
        q = np.array([0.5, 0.3, 0.2])
        
        js_div = compute_js_divergence(p, q)
        
        self.assertAlmostEqual(js_div, 0.0, places=10)

    def test_js_divergence_symmetry(self):
        """JS divergence should be symmetric: JS(P||Q) == JS(Q||P)."""
        p = np.array([0.7, 0.2, 0.1])
        q = np.array([0.1, 0.3, 0.6])
        
        js_pq = compute_js_divergence(p, q)
        js_qp = compute_js_divergence(q, p)
        
        self.assertAlmostEqual(js_pq, js_qp, places=10)

    def test_js_divergence_bounded(self):
        """JS divergence should be bounded in [0, 1] for base 2."""
        # Maximum divergence: completely disjoint supports
        p = np.array([1.0, 0.0, 0.0])
        q = np.array([0.0, 1.0, 0.0])
        
        js_div = compute_js_divergence(p, q)
        
        self.assertGreaterEqual(js_div, 0.0)
        self.assertLessEqual(js_div, 1.0)

    def test_js_divergence_non_disjoint(self):
        """JS divergence for non-disjoint distributions."""
        p = np.array([0.8, 0.2, 0.0])
        q = np.array([0.2, 0.8, 0.0])
        
        js_div = compute_js_divergence(p, q)
        
        # Should be between 0 and 1, and greater than 0
        self.assertGreater(js_div, 0.0)
        self.assertLess(js_div, 1.0)

    def test_js_divergence_with_small_values(self):
        """JS divergence handles small probability values correctly."""
        p = np.array([0.99, 0.01, 0.0])
        q = np.array([0.01, 0.99, 0.0])
        
        js_div = compute_js_divergence(p, q)
        
        self.assertGreater(js_div, 0.0)
        self.assertLessEqual(js_div, 1.0)

    def test_js_divergence_uniform_distributions(self):
        """JS divergence for uniform distributions should be 0."""
        n = 5
        p = np.ones(n) / n
        q = np.ones(n) / n
        
        js_div = compute_js_divergence(p, q)
        
        self.assertAlmostEqual(js_div, 0.0, places=10)

    def test_js_divergence_multidimensional(self):
        """JS divergence works for larger dimension vectors."""
        np.random.seed(123)
        p = np.random.dirichlet([1.0] * 10)
        q = np.random.dirichlet([1.0] * 10)
        
        js_div = compute_js_divergence(p, q)
        
        self.assertGreaterEqual(js_div, 0.0)
        self.assertLessEqual(js_div, 1.0)

    def test_validate_probability_vector_valid(self):
        """Validation passes for valid probability vectors."""
        p = np.array([0.2, 0.3, 0.5])
        self.assertTrue(validate_probability_vector(p))

    def test_validate_probability_vector_sum_not_one(self):
        """Validation fails for vectors that don't sum to 1."""
        p = np.array([0.2, 0.3, 0.6])  # sums to 1.1
        self.assertFalse(validate_probability_vector(p))

    def test_validate_probability_vector_negative(self):
        """Validation fails for vectors with negative values."""
        p = np.array([0.2, -0.1, 0.9])
        self.assertFalse(validate_probability_vector(p))

    def test_validate_probability_vector_zero_sum(self):
        """Validation fails for zero vector."""
        p = np.array([0.0, 0.0, 0.0])
        self.assertFalse(validate_probability_vector(p))

    def test_js_divergence_with_epsilon_smoothing(self):
        """JS divergence handles near-zero values without numerical issues."""
        # Very small values that might cause log(0) issues without smoothing
        p = np.array([1.0 - 1e-10, 1e-10, 0.0])
        q = np.array([1e-10, 1.0 - 1e-10, 0.0])
        
        js_div = compute_js_divergence(p, q)
        
        # Should compute without error and be in valid range
        self.assertGreaterEqual(js_div, 0.0)
        self.assertLessEqual(js_div, 1.0)


if __name__ == '__main__':
    unittest.main()