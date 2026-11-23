"""
Unit test for Bonferroni Correction Verification (Task T048).

This test verifies that the stats module's bonferroni_correction function
correctly implements the Bonferroni adjustment (p * N_tests) as mandated
by the project's Constitution Principle VII and Amendment 001.

It uses a known dataset (synthetic but mathematically exact) to ensure
the adjusted p-values match manual calculations exactly.
"""
import pytest
import sys
import os
import math

# Add project root to path to import stats module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from stats import bonferroni_correction


class TestBonferroniVerification:
    """Test suite to verify Bonferroni correction logic against manual calculation."""

    def test_bonferroni_single_test(self):
        """Verify correction with a single test (N=1)."""
        p_values = [0.05]
        adjusted = bonferroni_correction(p_values)
        
        # Manual calculation: 0.05 * 1 = 0.05
        expected = [0.05]
        
        assert len(adjusted) == 1
        assert math.isclose(adjusted[0], expected[0], rel_tol=1e-9)

    def test_bonferroni_multiple_tests(self):
        """Verify correction with multiple tests (N=5)."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        adjusted = bonferroni_correction(p_values)
        
        # Manual calculation: p * 5
        expected = [0.01 * 5, 0.02 * 5, 0.03 * 5, 0.04 * 5, 0.05 * 5]
        
        assert len(adjusted) == 5
        for i, (adj, exp) in enumerate(zip(adjusted, expected)):
            assert math.isclose(adj, exp, rel_tol=1e-9), f"Index {i}: {adj} != {exp}"

    def test_bonferroni_capped_at_one(self):
        """Verify that adjusted p-values are capped at 1.0."""
        p_values = [0.5, 0.6, 0.7]
        adjusted = bonferroni_correction(p_values)
        
        # Manual calculation without cap: [2.5, 3.0, 3.5]
        # With cap: [1.0, 1.0, 1.0]
        expected = [1.0, 1.0, 1.0]
        
        assert len(adjusted) == 3
        for i, (adj, exp) in enumerate(zip(adjusted, expected)):
            assert math.isclose(adj, exp, rel_tol=1e-9), f"Index {i}: {adj} != {exp}"

    def test_bonferroni_known_dataset_exact_match(self):
        """
        Verify against a known dataset of p-values to ensure exact match
        with manual Bonferroni calculation.
        
        Dataset: 10 p-values from a hypothetical correlation analysis.
        """
        # Known p-values from a correlation analysis (N=10 tests)
        p_values = [
            0.001, 0.012, 0.035, 0.048, 0.052,
            0.075, 0.089, 0.105, 0.120, 0.150
        ]
        n_tests = len(p_values)
        
        adjusted = bonferroni_correction(p_values)
        
        # Manual calculation: p * N, capped at 1.0
        expected = []
        for p in p_values:
            adj_p = p * n_tests
            if adj_p > 1.0:
                adj_p = 1.0
            expected.append(adj_p)
        
        # Verify exact match
        assert len(adjusted) == len(expected)
        for i, (adj, exp) in enumerate(zip(adjusted, expected)):
            assert math.isclose(adj, exp, rel_tol=1e-9), (
                f"Mismatch at index {i}: "
                f"Function returned {adj}, expected {exp} "
                f"(original p={p_values[i]}, N={n_tests})"
            )

    def test_bonferroni_empty_list(self):
        """Verify behavior with an empty list of p-values."""
        p_values = []
        adjusted = bonferroni_correction(p_values)
        assert adjusted == []

    def test_bonferroni_zero_p_value(self):
        """Verify behavior with a p-value of 0."""
        p_values = [0.0, 0.05]
        adjusted = bonferroni_correction(p_values)
        
        # 0 * N = 0
        assert math.isclose(adjusted[0], 0.0, rel_tol=1e-9)
        assert adjusted[1] == 0.05 * 2  # Assuming N=2

    def test_bonferroni_very_small_p_value(self):
        """Verify behavior with very small p-values (e.g., 1e-10)."""
        p_values = [1e-10, 1e-5]
        n_tests = 2
        adjusted = bonferroni_correction(p_values)
        
        # Expected: [2e-10, 2e-5]
        expected = [2e-10, 2e-5]
        
        for i, (adj, exp) in enumerate(zip(adjusted, expected)):
            assert math.isclose(adj, exp, rel_tol=1e-9)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])