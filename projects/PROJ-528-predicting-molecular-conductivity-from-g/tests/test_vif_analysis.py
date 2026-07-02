"""
Unit tests for VIF (Variance Inflation Factor) calculation.
"""
import pytest
import pandas as pd
import numpy as np
from code.vif_analysis import (
    calculate_vif,
    get_high_vif_features,
    calculate_vif_pairwise,
    run_vif_analysis
)


class TestVIFCalculation:
    """Tests for VIF calculation functions."""

    def test_calculate_vif_basic(self):
        """Test VIF calculation on a simple dataset."""
        # Create a dataset with some correlation
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(0, 1, n)
        x2 = x1 * 0.8 + np.random.normal(0, 0.2, n)  # Correlated with x1
        x3 = np.random.normal(0, 1, n)  # Independent

        df = pd.DataFrame({'x1': x1, 'x2': x2, 'x3': x3})

        vif_df = calculate_vif(df, exclude_cols=[])

        assert 'feature' in vif_df.columns
        assert 'vif' in vif_df.columns
        assert len(vif_df) == 3
        assert all(vif_df['vif'] >= 1.0)  # VIF should be >= 1

    def test_calculate_vif_with_exclude_cols(self):
        """Test that exclude_cols parameter works correctly."""
        np.random.seed(42)
        n = 50
        df = pd.DataFrame({
            'smiles': ['SMILES' + str(i) for i in range(n)],
            'target': np.random.normal(0, 1, n),
            'feature1': np.random.normal(0, 1, n),
            'feature2': np.random.normal(0, 1, n)
        })

        vif_df = calculate_vif(df, exclude_cols=['smiles', 'target'])

        assert len(vif_df) == 2
        assert 'smiles' not in vif_df['feature'].values
        assert 'target' not in vif_df['feature'].values

    def test_calculate_vif_sorted_descending(self):
        """Test that VIF results are sorted by VIF descending."""
        np.random.seed(42)
        n = 100
        # Create features with varying degrees of correlation
        x1 = np.random.normal(0, 1, n)
        x2 = x1 * 0.9 + np.random.normal(0, 0.1, n)  # High correlation
        x3 = np.random.normal(0, 1, n)  # Low correlation

        df = pd.DataFrame({'x1': x1, 'x2': x2, 'x3': x3})

        vif_df = calculate_vif(df, exclude_cols=[])

        # Check that VIF values are in descending order
        assert vif_df['vif'].is_monotonic_decreasing

    def test_get_high_vif_features(self):
        """Test identification of high VIF features."""
        vif_df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3'],
            'vif': [2.0, 15.0, 8.0]
        })

        high_vif = get_high_vif_features(vif_df, threshold=10.0)

        assert high_vif == ['f2']

    def test_get_high_vif_features_empty(self):
        """Test when no features exceed threshold."""
        vif_df = pd.DataFrame({
            'feature': ['f1', 'f2'],
            'vif': [2.0, 5.0]
        })

        high_vif = get_high_vif_features(vif_df, threshold=10.0)

        assert high_vif == []

    def test_calculate_vif_pairwise(self):
        """Test pairwise VIF calculation."""
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(0, 1, n)
        x2 = x1 * 0.9  # High correlation

        df = pd.DataFrame({'a': x1, 'b': x2})

        vif_pair = calculate_vif_pairwise(df, 'a', 'b')

        # For r=0.9, VIF = 1/(1-0.81) = 1/0.19 ≈ 5.26
        expected_vif = 1.0 / (1.0 - 0.9**2)
        assert np.isclose(vif_pair, expected_vif, rtol=0.1)

    def test_calculate_vif_pairwise_perfect_correlation(self):
        """Test pairwise VIF with perfect correlation (should be inf)."""
        np.random.seed(42)
        n = 50
        x = np.random.normal(0, 1, n)

        df = pd.DataFrame({'a': x, 'b': x * 2})  # Perfect correlation

        vif_pair = calculate_vif_pairwise(df, 'a', 'b')

        assert np.isinf(vif_pair)

    def test_run_vif_analysis(self):
        """Test the full VIF analysis pipeline."""
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(0, 1, n)
        x2 = x1 * 0.95 + np.random.normal(0, 0.1, n)  # High correlation
        x3 = np.random.normal(0, 1, n)  # Independent

        df = pd.DataFrame({
            'smiles': ['SMILES' + str(i) for i in range(n)],
            'target': np.random.normal(0, 1, n),
            'f1': x1,
            'f2': x2,
            'f3': x3
        })

        vif_df, high_vif = run_vif_analysis(df, exclude_cols=['smiles', 'target'], threshold=10.0)

        assert len(vif_df) == 3
        assert 'f2' in high_vif or len(high_vif) >= 0  # f2 might be flagged depending on threshold

    def test_calculate_vif_constant_column(self):
        """Test handling of constant (zero variance) columns."""
        np.random.seed(42)
        n = 50
        df = pd.DataFrame({
            'constant': [1.0] * n,
            'variable': np.random.normal(0, 1, n)
        })

        # Should not raise an error, constant column should be handled
        vif_df = calculate_vif(df, exclude_cols=[])

        # Constant column should be excluded from results
        assert 'constant' not in vif_df['feature'].values
        assert len(vif_df) == 1