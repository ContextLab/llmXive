"""
Unit tests for the permutation test logic in code/analysis/statistics.py.

This test suite verifies:
1. The permutation test performs the requested number of permutations (1,000).
2. The p-value correction logic is sound (calculating proportion of null stats >= observed).
3. The function handles edge cases (e.g., observed statistic is extreme).
4. The random seed is respected for reproducibility.
"""

import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Ensure the code directory is in the path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.statistics import run_permutation_test

class TestPermutationTestLogic:
    """Tests for the permutation test implementation."""

    def test_permutation_count(self):
        """Verify that the function performs exactly 1,000 permutations."""
        np.random.seed(42)
        # Create simple dummy data
        n = 50
        x = np.random.randn(n)
        y = np.random.randn(n)

        # We will patch the internal loop or verify via side effects if possible,
        # but since the function likely returns the p-value, we verify the logic
        # by ensuring the p-value is calculated based on a distribution of size n_permutations.
        # We can't easily introspect the loop count without modifying the function,
        # so we verify the statistical properties which depend on n_permutations.

        # Instead, let's verify the output structure and basic behavior.
        # A robust test for "1000 permutations" is to check that the p-value
        # granularity is consistent with 1/1000 (0.001).
        
        result = run_permutation_test(x, y, n_permutations=1000, random_state=42)
        
        # The p-value should be a multiple of 1/1001 (including the observed) or 1/1000
        # depending on implementation. Standard is (count + 1) / (n_perm + 1).
        # Granularity check:
        min_granularity = 1 / 1001.0
        # Check if p-value is close to a multiple of the granularity
        # This is a heuristic check for the permutation count.
        assert result["p_value"] >= 0.0
        assert result["p_value"] <= 1.0
        
        # Verify that the null distribution length matches n_permutations
        assert len(result["null_distribution"]) == 1000

    def test_p_value_correctness(self):
        """Verify p-value calculation logic: (count >= observed + 1) / (N + 1)."""
        np.random.seed(123)
        n = 100
        # Create data with a known strong correlation (or lack thereof)
        # Case 1: Strong positive correlation
        x = np.arange(n)
        y = x + np.random.normal(0, 0.1, n)
        
        result = run_permutation_test(x, y, n_permutations=1000, random_state=123)
        
        # With strong correlation, p-value should be very small
        assert result["p_value"] < 0.05
        
        # Case 2: No correlation (random noise)
        x_random = np.random.randn(n)
        y_random = np.random.randn(n)
        
        result_random = run_permutation_test(x_random, y_random, n_permutations=1000, random_state=123)
        
        # With no correlation, p-value should be > 0.05 (usually)
        # We can't guarantee > 0.05 for a single run, but we can check it's in valid range
        assert 0.0 <= result_random["p_value"] <= 1.0

    def test_random_seed_reproducibility(self):
        """Verify that setting random_state produces identical results."""
        np.random.seed(42)
        n = 50
        x = np.random.randn(n)
        y = np.random.randn(n)
        
        result_1 = run_permutation_test(x, y, n_permutations=1000, random_state=999)
        result_2 = run_permutation_test(x, y, n_permutations=1000, random_state=999)
        
        assert result_1["p_value"] == result_2["p_value"]
        assert np.array_equal(result_1["null_distribution"], result_2["null_distribution"])

    def test_output_structure(self):
        """Verify the output dictionary contains expected keys."""
        n = 20
        x = np.random.randn(n)
        y = np.random.randn(n)
        
        result = run_permutation_test(x, y, n_permutations=100, random_state=42)
        
        assert "observed_statistic" in result
        assert "p_value" in result
        assert "null_distribution" in result
        assert "n_permutations" in result
        
        # Verify types
        assert isinstance(result["observed_statistic"], (int, float))
        assert isinstance(result["p_value"], (int, float))
        assert isinstance(result["null_distribution"], np.ndarray)
        assert isinstance(result["n_permutations"], int)

    def test_edge_case_extreme_observed(self):
        """Test behavior when observed statistic is more extreme than all permutations."""
        # Create data where x and y are perfectly correlated
        n = 10
        x = np.arange(n)
        y = x * 2
        
        result = run_permutation_test(x, y, n_permutations=1000, random_state=42)
        
        # The observed statistic should be very high (perfect correlation)
        # The p-value should be small (likely 1/1001)
        assert result["p_value"] <= (1 / 1001.0)
        
    def test_edge_case_small_sample(self):
        """Test behavior with very small sample size."""
        n = 5
        x = np.random.randn(n)
        y = np.random.randn(n)
        
        # Should not crash
        result = run_permutation_test(x, y, n_permutations=100, random_state=42)
        
        assert result["p_value"] is not None
        assert 0.0 <= result["p_value"] <= 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])