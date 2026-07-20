"""
Unit tests for code/analysis/stats.py edge cases.

This module tests specific edge cases:
1. Collinearity (VIF calculation with perfect/multi-collinearity)
2. NaN/Inf handling in statistical functions
3. Empty or single-row datasets
4. Zero-variance predictors
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.stats import (
    calculate_vif,
    apply_fdr_correction,
    run_power_analysis,
    run_ancova_analysis
)
from config import Config


class TestCollinearityEdgeCases:
    """Tests for collinearity detection and VIF calculation."""

    def test_perfect_collinearity_raises_warning(self):
        """Test that perfect collinearity (duplicate column) is handled."""
        # Create dataframe with perfect collinearity (X1 and X2 are identical)
        data = pd.DataFrame({
            'target': [1.0, 2.0, 3.0, 4.0, 5.0],
            'X1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'X2': [1.0, 2.0, 3.0, 4.0, 5.0],  # Perfectly collinear with X1
            'X3': [5.0, 4.0, 3.0, 2.0, 1.0]
        })

        # VIF for X1 or X2 should be infinite or extremely large
        # The function should handle this without crashing
        vif_results = calculate_vif(data, 'target')
        
        # At least one of the collinear variables should have very high VIF
        high_vif_count = sum(1 for v in vif_results.values() if v > 100 or np.isinf(v))
        assert high_vif_count >= 1, "Perfect collinearity should result in high VIF"

    def test_zero_variance_predictor(self):
        """Test handling of zero-variance predictors."""
        data = pd.DataFrame({
            'target': [1.0, 2.0, 3.0, 4.0, 5.0],
            'X1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'X2': [5.0, 5.0, 5.0, 5.0, 5.0]  # Zero variance
        })

        # Should handle without crashing, likely returning NaN or inf for X2
        vif_results = calculate_vif(data, 'target')
        
        # X2 should have NaN or Inf VIF due to zero variance
        x2_vif = vif_results.get('X2', np.nan)
        assert np.isnan(x2_vif) or np.isinf(x2_vif), "Zero variance should result in NaN/Inf VIF"

    def test_multicollinearity_moderate(self):
        """Test moderate multicollinearity (correlation ~0.8)."""
        np.random.seed(42)
        n = 50
        X1 = np.random.randn(n)
        X2 = X1 * 0.8 + np.random.randn(n) * 0.2  # Correlated with X1
        X3 = np.random.randn(n)
        
        data = pd.DataFrame({
            'target': X1 + X3 + np.random.randn(n) * 0.1,
            'X1': X1,
            'X2': X2,
            'X3': X3
        })

        vif_results = calculate_vif(data, 'target')
        
        # X1 and X2 should have elevated VIF (> 2.5 for moderate correlation)
        assert vif_results['X1'] > 2.0, "Moderate collinearity should show elevated VIF"
        assert vif_results['X2'] > 2.0, "Moderate collinearity should show elevated VIF"


class TestNaNInfHandling:
    """Tests for NaN and Infinity handling in statistical functions."""

    def test_input_with_nan_values(self):
        """Test that functions handle inputs containing NaN."""
        data = pd.DataFrame({
            'target': [1.0, np.nan, 3.0, 4.0, 5.0],
            'X1': [1.0, 2.0, 3.0, np.nan, 5.0],
            'X2': [2.0, 3.0, 4.0, 5.0, 6.0]
        })

        # VIF calculation should handle NaN (either drop rows or return NaN VIF)
        vif_results = calculate_vif(data, 'target')
        
        # Should not crash; results should be valid numbers or NaN
        for var, vif_val in vif_results.items():
            assert isinstance(vif_val, (int, float, np.floating))
            assert not np.isinf(vif_val) or np.isnan(vif_val), "VIF should not be infinite unless expected"

    def test_fdr_with_all_nan_pvalues(self):
        """Test FDR correction when all p-values are NaN."""
        p_values = pd.Series([np.nan, np.nan, np.nan])
        
        # Should handle gracefully without crashing
        corrected = apply_fdr_correction(p_values)
        
        # Result should be all NaN or handle appropriately
        assert len(corrected) == len(p_values)

    def test_fdr_with_inf_pvalues(self):
        """Test FDR correction with infinity values."""
        p_values = pd.Series([0.01, np.inf, 0.05, 0.10])
        
        corrected = apply_fdr_correction(p_values)
        
        # Should not crash; inf should be handled
        assert len(corrected) == len(p_values)

    def test_power_analysis_with_nan_sample_size(self):
        """Test power analysis with NaN sample size."""
        # run_power_analysis expects valid inputs, but should handle edge cases
        # We test that it doesn't crash on invalid inputs
        with pytest.raises((ValueError, TypeError)):
            # This should fail gracefully, not crash with obscure error
            run_power_analysis(effect_size=0.5, n=np.nan, alpha=0.05)


class TestEmptyAndSmallDatasets:
    """Tests for empty and very small datasets."""

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        data = pd.DataFrame(columns=['target', 'X1', 'X2'])
        
        # VIF on empty data should handle gracefully
        with pytest.raises((ValueError, IndexError)):
            calculate_vif(data, 'target')

    def test_single_row_dataframe(self):
        """Test handling of single-row dataframe (insufficient for regression)."""
        data = pd.DataFrame({
            'target': [1.0],
            'X1': [2.0],
            'X2': [3.0]
        })
        
        # VIF requires at least 2 rows (degrees of freedom)
        with pytest.raises((ValueError, IndexError)):
            calculate_vif(data, 'target')

    def test_two_rows_dataframe(self):
        """Test handling of minimal valid dataframe (2 rows)."""
        data = pd.DataFrame({
            'target': [1.0, 2.0],
            'X1': [2.0, 3.0]
        })
        
        # This is the minimum for VIF calculation
        vif_results = calculate_vif(data, 'target')
        assert len(vif_results) == 1
        assert 'X1' in vif_results

    def test_power_analysis_minimum_n(self):
        """Test power analysis with minimum N (should return high required N)."""
        # With very small N, the minimum required N should be large
        result = run_power_analysis(effect_size=0.5, n=5, alpha=0.05)
        
        # The minimum N required should be >= current N
        assert result['min_n_required'] >= 5, "Minimum N required should be at least current N"


class TestStatisticalBounds:
    """Tests for statistical value bounds and sanity checks."""

    def test_fdr_pvalues_in_bounds(self):
        """Test that FDR-corrected p-values are in [0, 1]."""
        p_values = pd.Series([0.01, 0.05, 0.10, 0.20, 0.50])
        
        corrected = apply_fdr_correction(p_values)
        
        for p in corrected:
            assert 0 <= p <= 1, f"FDR-corrected p-value {p} out of bounds [0, 1]"

    def test_vif_non_negative(self):
        """Test that VIF values are non-negative."""
        np.random.seed(42)
        data = pd.DataFrame({
            'target': np.random.randn(50),
            'X1': np.random.randn(50),
            'X2': np.random.randn(50),
            'X3': np.random.randn(50)
        })
        
        vif_results = calculate_vif(data, 'target')
        
        for var, vif_val in vif_results.items():
            assert vif_val >= 0, f"VIF for {var} is negative: {vif_val}"

    def test_ancova_with_all_identical_predictors(self):
        """Test ANCOVA with all identical predictors (degenerate case)."""
        data = pd.DataFrame({
            'post_treatment_score': [1.0, 2.0, 3.0, 4.0, 5.0],
            'pre_treatment_score': [1.0, 1.0, 1.0, 1.0, 1.0],  # All identical
            'modularity': [2.0, 3.0, 4.0, 5.0, 6.0]
        })
        
        # Should handle degenerate case without crashing
        # May return NaN coefficients or raise a warning
        with pytest.raises((ValueError, np.linalg.LinAlgError)):
            run_ancova_analysis(data, 'post_treatment_score', 'modularity')


class TestIntegrationEdgeCases:
    """Integration tests combining multiple edge cases."""

    def test_real_world_missing_data_pattern(self):
        """Test with realistic missing data pattern (MCAR)."""
        np.random.seed(42)
        n = 100
        
        # Generate data with ~10% missing completely at random
        data = pd.DataFrame({
            'post': np.random.randn(n),
            'pre': np.random.randn(n),
            'modularity': np.random.randn(n),
            'fd': np.random.randn(n)
        })
        
        # Introduce missing values
        mask = np.random.rand(n, 4) < 0.1
        data_array = data.values
        data_array[mask] = np.nan
        data = pd.DataFrame(data_array, columns=data.columns)
        
        # VIF should handle missing data (either by dropping or returning NaN)
        vif_results = calculate_vif(data, 'post')
        
        # Should not crash; results should be valid
        assert len(vif_results) == 3  # pre, modularity, fd

    def test_highly_correlated_covariates(self):
        """Test with highly correlated covariates (real-world scenario)."""
        np.random.seed(42)
        n = 50
        
        # Motion parameters often correlated
        fd = np.random.randn(n)
        fd_c = fd * 0.9 + np.random.randn(n) * 0.1  # Highly correlated
        
        data = pd.DataFrame({
            'post': np.random.randn(n),
            'pre': np.random.randn(n),
            'modularity': np.random.randn(n),
            'fd': fd,
            'fd_c': fd_c
        })
        
        vif_results = calculate_vif(data, 'post')
        
        # fd and fd_c should have high VIF due to correlation
        assert vif_results['fd'] > 5 or vif_results['fd_c'] > 5, \
            "Highly correlated covariates should show elevated VIF"

    def test_outlier_influence_on_vif(self):
        """Test VIF robustness to outliers."""
        np.random.seed(42)
        n = 50
        
        data = pd.DataFrame({
            'target': np.random.randn(n),
            'X1': np.random.randn(n),
            'X2': np.random.randn(n)
        })
        
        # Add extreme outlier
        data.loc[0, 'X1'] = 1000
        data.loc[0, 'X2'] = 1000
        
        # VIF should still be calculable (though potentially inflated by outlier)
        vif_results = calculate_vif(data, 'target')
        
        # Should not crash
        assert len(vif_results) == 2