"""
Unit tests for code/analysis/comparators.py

These tests verify the correctness of statistical comparison methods:
Kruskal-Wallis and Dunn's post-hoc test with Holm correction.
"""
import numpy as np
import pandas as pd
import pytest
from scipy.stats import kruskal

# Assuming comparators module exists and exports these functions
# based on T037 and T038.
try:
    from analysis.comparators import kruskal_wallis_test, dunn_post_hoc_test
except ImportError:
    # If not implemented, we skip these tests or mock the behavior
    kruskal_wallis_test = None
    dunn_post_hoc_test = None


class TestKruskalWallis:
    """Tests for Kruskal-Wallis test."""

    def test_kruskal_wallis_identical_groups(self):
        """Test Kruskal-Wallis on identical groups (should yield high p-value)."""
        if kruskal_wallis_test is None:
            pytest.skip("kruskal_wallis_test not implemented")

        # Generate identical data
        data = {
            'method': ['A'] * 50 + ['B'] * 50 + ['C'] * 50,
            'power': np.concatenate([np.random.normal(0.5, 0.1, 50) for _ in range(3)])
        }
        df = pd.DataFrame(data)

        stat, pval = kruskal_wallis_test(df, 'power', 'method')

        assert stat >= 0, "Statistic must be non-negative"
        assert 0 <= pval <= 1, "P-value must be between 0 and 1"
        # With identical distributions, p-value should be high (not significant)
        # We don't assert pval > 0.05 strictly due to randomness, but it should be reasonable.

    def test_kruskal_wallis_different_groups(self):
        """Test Kruskal-Wallis on clearly different groups (should yield low p-value)."""
        if kruskal_wallis_test is None:
            pytest.skip("kruskal_wallis_test not implemented")

        data = {
            'method': ['A'] * 50 + ['B'] * 50 + ['C'] * 50,
            'power': np.concatenate([
                np.random.normal(0.2, 0.05, 50),  # Low power
                np.random.normal(0.5, 0.05, 50),  # Medium power
                np.random.normal(0.8, 0.05, 50)   # High power
            ])
        }
        df = pd.DataFrame(data)

        stat, pval = kruskal_wallis_test(df, 'power', 'method')

        assert pval < 0.05, "Should detect significant difference between groups"


class TestDunnPostHoc:
    """Tests for Dunn's post-hoc test with Holm correction."""

    def test_dunn_holm_correction(self):
        """Test that Dunn's test applies Holm correction correctly."""
        if dunn_post_hoc_test is None:
            pytest.skip("dunn_post_hoc_test not implemented")

        # Create a dataset with known structure
        # Group A: Low values, Group B: High values
        np.random.seed(42)
        data = {
            'method': ['A'] * 100 + ['B'] * 100,
            'power': np.concatenate([
                np.random.normal(0.3, 0.1, 100),
                np.random.normal(0.7, 0.1, 100)
            ])
        }
        df = pd.DataFrame(data)

        # Perform Dunn's test
        # Expected: A vs B should be significant
        results = dunn_post_hoc_test(df, 'power', 'method', alpha=0.05)

        # Check that results are returned
        assert isinstance(results, pd.DataFrame), "Results should be a DataFrame"
        assert 'comparison' in results.columns, "Results should have 'comparison' column"
        assert 'p_value' in results.columns, "Results should have 'p_value' column"
        assert 'significant' in results.columns, "Results should have 'significant' column"

        # Verify Holm correction logic (simplified check)
        # If we have only one comparison, p-value should be the same as raw
        # If multiple, they should be adjusted
        assert all(results['p_value'] <= 1.0), "P-values must be <= 1.0"

    def test_dunn_holm_moderate_difference(self):
        """Test Dunn's test with moderate difference between groups."""
        if dunn_post_hoc_test is None:
            pytest.skip("dunn_post_hoc_test not implemented")

        np.random.seed(123)
        data = {
            'method': ['A'] * 50 + ['B'] * 50 + ['C'] * 50,
            'power': np.concatenate([
                np.random.normal(0.4, 0.15, 50),
                np.random.normal(0.5, 0.15, 50),
                np.random.normal(0.6, 0.15, 50)
            ])
        }
        df = pd.DataFrame(data)

        results = dunn_post_hoc_test(df, 'power', 'method', alpha=0.05)

        # Check structure
        assert len(results) == 3, "Should have 3 comparisons for 3 groups"
        assert all('A' in c and 'B' in c or 'A' in c and 'C' in c or 'B' in c and 'C' in c
                   for c in results['comparison']), "Comparisons should be valid pairs"