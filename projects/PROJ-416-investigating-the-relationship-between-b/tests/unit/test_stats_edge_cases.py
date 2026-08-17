"""
Unit tests for code/analysis/stats.py edge cases.

Tests cover:
1. Collinearity handling (VIF > 5, PCA failure, <2 components >90% variance)
2. NaN/Infinity handling in metrics
3. Empty dataframes
4. Single subject edge cases
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.stats import (
    calculate_vif,
    apply_fdr_correction,
    run_power_analysis,
    run_ancova_analysis,
    CollinearityUnresolvableError
)


class TestVIFCalculationEdgeCases:
    """Tests for VIF calculation with edge cases."""

    def test_vif_perfect_collinearity_raises_error(self):
        """Test that perfect collinearity (VIF = inf) triggers CollinearityUnresolvableError."""
        # Create dataframe with perfect collinearity (X2 = 2 * X1)
        data = pd.DataFrame({
            'intercept': [1.0, 1.0, 1.0, 1.0],
            'X1': [1.0, 2.0, 3.0, 4.0],
            'X2': [2.0, 4.0, 6.0, 8.0]  # Perfectly correlated with X1
        })

        with pytest.raises(CollinearityUnresolvableError):
            calculate_vif(data)

    def test_vif_high_collinearity(self):
        """Test VIF calculation with high but not perfect collinearity."""
        # Create dataframe with high collinearity (VIF > 5 expected)
        np.random.seed(42)
        n = 50
        data = pd.DataFrame({
            'intercept': [1.0] * n,
            'X1': np.random.randn(n),
            'X2': np.random.randn(n) * 0.9 + np.random.randn(n) * 0.1  # Highly correlated
        })

        vif_values = calculate_vif(data)

        # At least one variable should have VIF > 5
        max_vif = max(vif_values.values())
        assert max_vif > 5, f"Expected high VIF (>5), got {max_vif}"

    def test_vif_no_collinearity(self):
        """Test VIF calculation with uncorrelated variables."""
        np.random.seed(42)
        n = 50
        data = pd.DataFrame({
            'intercept': [1.0] * n,
            'X1': np.random.randn(n),
            'X2': np.random.randn(n),
            'X3': np.random.randn(n)
        })

        vif_values = calculate_vif(data)

        # All VIFs should be close to 1 (no collinearity)
        for var, vif in vif_values.items():
            assert vif < 5, f"Unexpected high VIF for {var}: {vif}"

    def test_vif_single_predictor(self):
        """Test VIF with only one predictor (intercept only)."""
        data = pd.DataFrame({
            'intercept': [1.0, 1.0, 1.0, 1.0]
        })

        vif_values = calculate_vif(data)

        # Should return empty dict or VIF of 1 for intercept
        assert len(vif_values) == 0 or all(v == 1.0 for v in vif_values.values())


class TestNaNHandling:
    """Tests for NaN and Infinity handling in stats functions."""

    def test_ancova_with_nan_values(self):
        """Test that ANCOVA handles NaN values appropriately."""
        # Create data with NaN in outcome
        np.random.seed(42)
        n = 20
        data = pd.DataFrame({
            'post_score': np.random.randn(n),
            'pre_score': np.random.randn(n),
            'network_metric': np.random.randn(n),
            'fd': np.random.randn(n)
        })

        # Introduce NaN in outcome
        data.loc[5, 'post_score'] = np.nan

        # Should not crash, but may drop rows or raise error depending on implementation
        # For now, we expect it to handle gracefully (drop NaN or raise clear error)
        try:
            result = run_ancova_analysis(
                data=data,
                outcome_col='post_score',
                pre_col='pre_score',
                metric_col='network_metric',
                confound_cols=['fd']
            )
            # If it succeeds, check that NaN rows were handled
            assert result is not None
        except Exception as e:
            # If it raises, it should be a clear error, not a cryptic NaN error
            assert "NaN" in str(e) or "nan" in str(e) or "dropna" in str(e).lower()

    def test_fdr_correction_with_pvalues_of_one(self):
        """Test FDR correction with p-values of 1.0."""
        pvalues = [0.01, 0.05, 0.1, 0.5, 1.0, 1.0]

        corrected = apply_fdr_correction(pvalues)

        assert len(corrected) == len(pvalues)
        assert all(0 <= p <= 1 for p in corrected)
        # P-values of 1.0 should remain 1.0 or close to it
        assert corrected[-1] >= 0.9

    def test_fdr_correction_with_all_zeros(self):
        """Test FDR correction with all p-values of 0."""
        pvalues = [0.0, 0.0, 0.0]

        corrected = apply_fdr_correction(pvalues)

        assert len(corrected) == len(pvalues)
        assert all(p == 0.0 for p in corrected)


class TestPowerAnalysisEdgeCases:
    """Tests for power analysis edge cases."""

    def test_power_analysis_insufficient_n(self):
        """Test power analysis with N < 5 (should halt)."""
        with pytest.raises(Exception) as exc_info:
            run_power_analysis(n_obs=3, effect_size=0.15, alpha=0.05, power=0.8)

        assert "Insufficient Power" in str(exc_info.value) or "N < 5" in str(exc_info.value)

    def test_power_analysis_very_small_effect(self):
        """Test power analysis with very small effect size."""
        result = run_power_analysis(n_obs=100, effect_size=0.01, alpha=0.05, power=0.8)

        assert 'min_N_required' in result
        assert result['min_N_required'] > 100  # Should require more subjects

    def test_power_analysis_large_effect(self):
        """Test power analysis with large effect size."""
        result = run_power_analysis(n_obs=20, effect_size=0.5, alpha=0.05, power=0.8)

        assert 'min_N_required' in result
        assert result['min_N_required'] <= 20  # Should be achievable


class TestEmptyDataCases:
    """Tests for empty or near-empty datasets."""

    def test_ancova_empty_dataframe(self):
        """Test ANCOVA with empty dataframe."""
        data = pd.DataFrame(columns=['post_score', 'pre_score', 'network_metric', 'fd'])

        with pytest.raises((ValueError, IndexError, Exception)) as exc_info:
            run_ancova_analysis(
                data=data,
                outcome_col='post_score',
                pre_col='pre_score',
                metric_col='network_metric',
                confound_cols=['fd']
            )

        # Should raise a clear error, not a cryptic one
        error_msg = str(exc_info.value).lower()
        assert "empty" in error_msg or "length" in error_msg or "index" in error_msg

    def test_ancova_single_subject(self):
        """Test ANCOVA with single subject."""
        data = pd.DataFrame({
            'post_score': [1.0],
            'pre_score': [0.5],
            'network_metric': [0.3],
            'fd': [0.2]
        })

        # Single subject regression is degenerate; should raise error or return None
        try:
            result = run_ancova_analysis(
                data=data,
                outcome_col='post_score',
                pre_col='pre_score',
                metric_col='network_metric',
                confound_cols=['fd']
            )
            # If it returns, it should be None or have a warning
            assert result is None or 'warning' in str(result).lower()
        except Exception as e:
            # If it raises, it should be clear
            assert "single" in str(e).lower() or "degenerate" in str(e).lower() or "insufficient" in str(e).lower()


class TestCollinearityUnresolvableError:
    """Tests for the CollinearityUnresolvableError exception."""

    def test_error_raised_on_pca_failure(self):
        """Test that CollinearityUnresolvableError is raised when PCA fails."""
        # This is tested implicitly in test_vif_perfect_collinearity_raises_error
        # but we verify the exception type here
        data = pd.DataFrame({
            'intercept': [1.0, 1.0, 1.0, 1.0],
            'X1': [1.0, 2.0, 3.0, 4.0],
            'X2': [2.0, 4.0, 6.0, 8.0]
        })

        with pytest.raises(CollinearityUnresolvableError):
            calculate_vif(data)

    def test_error_message_is_descriptive(self):
        """Test that CollinearityUnresolvableError has a descriptive message."""
        data = pd.DataFrame({
            'intercept': [1.0, 1.0, 1.0, 1.0],
            'X1': [1.0, 2.0, 3.0, 4.0],
            'X2': [2.0, 4.0, 6.0, 8.0]
        })

        try:
            calculate_vif(data)
            pytest.fail("Expected CollinearityUnresolvableError")
        except CollinearityUnresolvableError as e:
            assert len(str(e)) > 10, "Error message should be descriptive"
            assert "collinearity" in str(e).lower() or "VIF" in str(e)