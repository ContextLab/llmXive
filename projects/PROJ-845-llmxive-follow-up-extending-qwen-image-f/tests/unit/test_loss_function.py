"""
Unit tests for loss functions used in the distillation pipeline.
Specifically tests KL-divergence implementation.
"""
import unittest
import math
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.metrics import compute_trace_entropy


class TestLossFunction(unittest.TestCase):
    """Tests for loss function implementations."""

    def test_kl_divergence_non_negative(self):
        """
        Test that KL-divergence implementation returns a non-negative scalar.
        
        KL divergence D_KL(P || Q) is always >= 0.
        This test verifies the mathematical property holds for our implementation.
        """
        # Create two identical distributions (should result in 0 KL divergence)
        identical_probs = [0.25, 0.25, 0.25, 0.25]
        result_identical = compute_trace_entropy(identical_probs, identical_probs)
        
        self.assertIsInstance(result_identical, float)
        self.assertGreaterEqual(result_identical, 0.0, 
                                "KL divergence between identical distributions should be 0")
        
        # Create two different distributions (should result in positive KL divergence)
        p_dist = [0.7, 0.2, 0.1, 0.0]
        q_dist = [0.1, 0.1, 0.1, 0.7]
        
        result_diff = compute_trace_entropy(p_dist, q_dist)
        
        self.assertIsInstance(result_diff, float)
        self.assertGreater(result_diff, 0.0, 
                           "KL divergence between different distributions should be positive")
        
        # Test with uniform distributions (should be 0)
        uniform_p = [0.5, 0.5]
        uniform_q = [0.5, 0.5]
        result_uniform = compute_trace_entropy(uniform_p, uniform_q)
        
        self.assertAlmostEqual(result_uniform, 0.0, places=10,
                               msg="KL divergence between uniform distributions should be 0")

    def test_kl_divergence_asymmetry(self):
        """
        Test that KL divergence is asymmetric: D_KL(P || Q) != D_KL(Q || P).
        """
        p_dist = [0.9, 0.1]
        q_dist = [0.1, 0.9]
        
        kl_pq = compute_trace_entropy(p_dist, q_dist)
        kl_qp = compute_trace_entropy(q_dist, p_dist)
        
        self.assertGreater(kl_pq, 0.0)
        self.assertGreater(kl_qp, 0.0)
        self.assertNotAlmostEqual(kl_pq, kl_qp, places=5,
                                  msg="KL divergence should be asymmetric")

    def test_kl_divergence_with_zeros(self):
        """
        Test behavior when Q has zeros (should handle gracefully or raise).
        """
        p_dist = [0.5, 0.5]
        q_dist = [1.0, 0.0]  # Q has a zero where P has probability
        
        # This should either return a large number or handle the edge case
        # Our implementation should handle this without crashing
        try:
            result = compute_trace_entropy(p_dist, q_dist)
            self.assertIsInstance(result, float)
            # If it returns a value, it should be non-negative
            self.assertGreaterEqual(result, 0.0)
        except (ValueError, ZeroDivisionError):
            # It's also acceptable to raise an error for invalid distributions
            pass


if __name__ == '__main__':
    unittest.main()