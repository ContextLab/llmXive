"""
Tests for the SCM Generator module.

Specifically tests the regenerate_ground_truth function for
Constitution Principle VI compliance.
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.simulation.scm_generator import regenerate_ground_truth


class TestRegenerateGroundTruth:
    """Test suite for the regenerate_ground_truth function."""
    
    def test_regenerate_ground_truth(self):
        """
        Test that regenerate_ground_truth returns expected values for seed=42, beta=0.5.
        
        According to T006 requirements:
        - For seed=42 and beta=0.5, the function must return tau_true=0.5 (hardcoded constant)
        - beta must be returned as 0.5 exactly
        """
        seed = 42
        beta = 0.5
        
        tau_true, beta_returned = regenerate_ground_truth(seed, beta)
        
        # Verify tau_true is exactly 0.5 as required by the test specification
        assert tau_true == 0.5, f"Expected tau_true=0.5, got {tau_true}"
        
        # Verify beta is returned exactly as provided
        assert beta_returned == 0.5, f"Expected beta=0.5, got {beta_returned}"
    
    def test_regenerate_ground_truth_deterministic(self):
        """
        Test that the function is deterministic: same inputs always produce same outputs.
        """
        seed = 123
        beta = 0.8
        
        # Run multiple times
        results = [regenerate_ground_truth(seed, beta) for _ in range(5)]
        
        # All results should be identical
        assert len(set(results)) == 1, "Function should be deterministic"
        
        # Verify the result is consistent
        expected_tau, expected_beta = results[0]
        for tau, b in results:
            assert tau == expected_tau
            assert b == expected_beta
    
    def test_regenerate_ground_truth_different_seeds(self):
        """
        Test that different seeds produce different tau_true values.
        """
        beta = 0.5
        
        tau1, _ = regenerate_ground_truth(100, beta)
        tau2, _ = regenerate_ground_truth(200, beta)
        
        # Different seeds should generally produce different tau values
        # (though theoretically possible to collide, it's extremely unlikely)
        assert tau1 != tau2, "Different seeds should produce different tau values"
    
    def test_regenerate_ground_truth_beta_preserved(self):
        """
        Test that the beta parameter is always returned unchanged.
        """
        test_cases = [
            (42, 0.0),
            (42, 0.2),
            (42, 1.0),
            (999, -0.5),
            (123, 2.5)
        ]
        
        for seed, beta in test_cases:
            tau, beta_returned = regenerate_ground_truth(seed, beta)
            assert beta_returned == beta, f"Beta should be preserved: expected {beta}, got {beta_returned}"