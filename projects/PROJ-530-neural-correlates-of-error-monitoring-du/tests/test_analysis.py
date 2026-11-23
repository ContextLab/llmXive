"""
Unit tests for analysis functions.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from analysis import calculate_vif, apply_bonferroni

# Configure logging
logging.basicConfig(level=logging.WARNING)

class TestVIFCalculation:
    """Tests for Variance Inflation Factor calculation."""

    def test_vif_calculation(self):
        """Verify that calculate_vif returns a value < 5 for uncorrelated predictors and >= 5 for perfectly correlated predictors."""
        
        # Test 1: Uncorrelated predictors (should be low VIF)
        # Create a dataframe with uncorrelated columns
        np.random.seed(42)
        n_samples = 100
        data_uncorrelated = pd.DataFrame({
            'x1': np.random.normal(0, 1, n_samples),
            'x2': np.random.normal(0, 1, n_samples),
            'x3': np.random.normal(0, 1, n_samples)
        })
        
        vif_values = calculate_vif(data_uncorrelated)
        
        # VIF for uncorrelated variables should be close to 1
        for var, vif in vif_values.items():
            assert vif < 5, f"VIF for {var} is {vif}, expected < 5 for uncorrelated data"
            assert vif >= 1, f"VIF cannot be less than 1, got {vif}"

        # Test 2: Perfectly correlated predictors (should be high VIF)
        # Create a dataframe with one column being a linear combination of others
        data_correlated = pd.DataFrame({
            'x1': np.random.normal(0, 1, n_samples),
            'x2': np.random.normal(0, 1, n_samples),
            'x3': np.random.normal(0, 1, n_samples)
        })
        # Make x3 perfectly correlated with x1 + x2
        data_correlated['x3'] = data_correlated['x1'] + data_correlated['x2'] + 0.0001  # Small noise to avoid singularity
        
        vif_values_correlated = calculate_vif(data_correlated)
        
        # At least one VIF should be high (>= 5) due to multicollinearity
        max_vif = max(vif_values_correlated.values())
        assert max_vif >= 5, f"Expected at least one VIF >= 5 for correlated data, got max {max_vif}"

class TestBonferroniCorrection:
    """Tests for Bonferroni correction."""

    def test_bonferroni_correction(self):
        """Verify that apply_bonferroni correctly divides alpha by the number of tests and adjusts p-values accordingly."""
        
        # Test data
        p_values = [0.01, 0.03, 0.05, 0.10, 0.20]
        alpha = 0.05
        
        corrected = apply_bonferroni(p_values, alpha)
        
        # Check that we have the same number of results
        assert len(corrected) == len(p_values)
        
        # Check that p-values are capped at 1.0
        for p_adj in corrected:
            assert 0 <= p_adj <= 1.0, f"Adjusted p-value {p_adj} out of range [0, 1]"
        
        # Check logic: p_adj = min(p * n, 1.0)
        n_tests = len(p_values)
        for i, p in enumerate(p_values):
            expected = min(p * n_tests, 1.0)
            assert np.isclose(corrected[i], expected), \
                f"For p={p}, expected {expected}, got {corrected[i]}"
        
        # Check significance threshold
        # Original alpha / n_tests
        adjusted_alpha = alpha / n_tests
        # Values below adjusted_alpha should be significant (p < alpha/n)
        # After correction, p_adj < alpha
        
        # p=0.01, n=5 -> p_adj = 0.05 (significant if alpha=0.05)
        # p=0.03, n=5 -> p_adj = 0.15 (not significant)
        assert corrected[0] <= alpha, "First p-value should be significant after correction"
        assert corrected[1] > alpha, "Second p-value should not be significant after correction"
