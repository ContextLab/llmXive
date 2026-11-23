import pytest
import numpy as np
import pandas as pd
import os
import json
import tempfile
from pathlib import Path
from scipy import stats

from code.validation import (
    apply_benjamini_hochberg_correction,
    calculate_univariate_correlations,
    save_bh_correction_results,
    run_permutation_test
)

class TestBenjaminiHochberg:
    def test_bh_correction_basic(self):
        """Test BH correction with known p-values."""
        p_values = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        q_values = apply_benjamini_hochberg_correction(p_values)
        
        # q-values should be >= p-values
        assert np.all(q_values >= p_values)
        # q-values should be <= 1.0
        assert np.all(q_values <= 1.0)
        # q-values should be non-decreasing when sorted by p-value
        sorted_indices = np.argsort(p_values)
        sorted_q = q_values[sorted_indices]
        assert np.all(np.diff(sorted_q) >= -1e-10)  # Allow small floating point errors

    def test_bh_correction_empty(self):
        """Test BH correction with empty array."""
        p_values = np.array([])
        q_values = apply_benjamini_hochberg_correction(p_values)
        assert len(q_values) == 0

    def test_bh_correction_single(self):
        """Test BH correction with single p-value."""
        p_values = np.array([0.05])
        q_values = apply_benjamini_hochberg_correction(p_values)
        assert len(q_values) == 1
        assert q_values[0] == 0.05  # Single p-value: q = p * n / 1 = p

    def test_bh_correction_monotonicity(self):
        """Test that BH correction maintains monotonicity."""
        p_values = np.array([0.001, 0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.3, 0.4])
        q_values = apply_benjamini_hochberg_correction(p_values)
        
        # After sorting by p-value, q-values should be non-decreasing
        sorted_indices = np.argsort(p_values)
        sorted_q = q_values[sorted_indices]
        
        for i in range(len(sorted_q) - 1):
            assert sorted_q[i] <= sorted_q[i+1] + 1e-10

class TestCorrelationCalculation:
    def test_correlation_calculation(self):
        """Test univariate correlation calculation."""
        n_samples = 50
        np.random.seed(42)
        
        # Create synthetic data with known correlation
        metabolite = np.random.randn(n_samples)
        target = 2 * metabolite + np.random.randn(n_samples) * 0.5
        
        df = pd.DataFrame({
            'metabolite_A': metabolite,
            'resistance': target
        })
        
        corr_df = calculate_univariate_correlations(df, 'resistance')
        
        assert len(corr_df) == 1
        assert 'metabolite_A' in corr_df['metabolite_name'].values
        assert 'correlation_coefficient' in corr_df.columns
        assert 'unadjusted_p_value' in corr_df.columns
        
        # Check that correlation is significant (r > 0.8 expected)
        assert corr_df['correlation_coefficient'].iloc[0] > 0.8

    def test_correlation_no_metabolites(self):
        """Test error when no metabolite columns found."""
        df = pd.DataFrame({'resistance': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="No metabolite columns found"):
            calculate_univariate_correlations(df, 'resistance')

class TestBHCorrectionSaving:
    def test_save_bh_correction(self):
        """Test saving BH-corrected results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'correlations.csv')
            
            df = pd.DataFrame({
                'metabolite_name': ['met_A', 'met_B', 'met_C'],
                'correlation_coefficient': [0.5, -0.3, 0.1],
                'unadjusted_p_value': [0.01, 0.05, 0.2]
            })
            
            save_bh_correction_results(df, output_path)
            
            assert os.path.exists(output_path)
            
            # Load and verify
            result_df = pd.read_csv(output_path)
            assert 'q_value' in result_df.columns
            assert 'significant' in result_df.columns
            assert len(result_df) == 3

class TestPermutationTest:
    def test_permutation_test_structure(self):
        """Test that permutation test returns expected structure."""
        np.random.seed(42)
        X = np.random.randn(30, 5)
        y = np.random.randn(30)
        
        null_dist, p_val = run_permutation_test(X, y, n_permutations=10, random_seed=42)
        
        assert len(null_dist) == 10
        assert isinstance(p_val, float)
        assert 0 <= p_val <= 1

    def test_permutation_test_significance(self):
        """Test permutation test detects significant correlation."""
        np.random.seed(42)
        n = 50
        X = np.random.randn(n, 10)
        # Create a strong signal in one feature
        X[:, 0] = np.random.randn(n)
        y = X[:, 0] * 2 + np.random.randn(n) * 0.1
        
        null_dist, p_val = run_permutation_test(X, y, n_permutations=100, random_seed=42)
        
        # With strong signal, p-value should be low
        assert p_val < 0.1

    def test_permutation_test_null(self):
        """Test permutation test with no signal."""
        np.random.seed(42)
        n = 50
        X = np.random.randn(n, 10)
        y = np.random.randn(n)
        
        null_dist, p_val = run_permutation_test(X, y, n_permutations=100, random_seed=42)
        
        # With no signal, p-value should be high (not significant)
        assert p_val > 0.05