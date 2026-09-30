"""
Unit tests for correlation analysis module.
"""
import pytest
import numpy as np
import pandas as pd
from scipy import stats
from unittest.mock import patch, MagicMock
import logging
from code.src.analysis.correlation import (
    calculate_skewness,
    shapiro_wilk_test,
    should_switch_to_spearman,
    pearson_correlation_with_ci,
    spearman_correlation_with_ci,
    apply_benjamini_hochberg,
    run_correlation_analysis,
    run_multiple_correlations
)

class TestCorrelationMethods:
    """Test correlation calculation methods."""
    
    def test_calculate_skewness_normal_data(self):
        """Test skewness calculation on normally distributed data."""
        np.random.seed(42)
        data = np.random.normal(loc=0, scale=1, size=1000)
        skewness = calculate_skewness(data)
        # For normal distribution, skewness should be close to 0
        assert abs(skewness) < 0.5

    def test_calculate_skewness_skewed_data(self):
        """Test skewness calculation on skewed data."""
        # Generate exponentially distributed data (right-skewed)
        data = np.random.exponential(scale=1.0, size=1000)
        skewness = calculate_skewness(data)
        # Exponential distribution has skewness of 2.0
        assert skewness > 1.5

    def test_shapiro_wilk_test_normal_data(self):
        """Test Shapiro-Wilk test on normally distributed data."""
        np.random.seed(42)
        data = np.random.normal(loc=0, scale=1, size=100)
        statistic, p_value = shapiro_wilk_test(data)
        # For normal data, p-value should be > 0.05 (fail to reject normality)
        assert p_value > 0.05

    def test_shapiro_wilk_test_non_normal_data(self):
        """Test Shapiro-Wilk test on non-normal data."""
        # Generate uniform data (less peaked than normal)
        data = np.random.uniform(low=0, high=1, size=100)
        statistic, p_value = shapiro_wilk_test(data)
        # For uniform data, p-value is often < 0.05
        # We just check that the function runs without error
        assert 0 <= p_value <= 1

    def test_should_switch_to_spearman_high_skewness(self):
        """Test auto-switch logic with highly skewed data."""
        # Generate highly skewed data
        x = np.random.exponential(scale=1.0, size=500)
        y = np.random.exponential(scale=1.0, size=500)
        
        should_switch = should_switch_to_spearman(x, y, skewness_threshold=1.0)
        assert should_switch is True

    def test_should_switch_to_spearman_normal_data(self):
        """Test auto-switch logic with normally distributed data."""
        np.random.seed(42)
        x = np.random.normal(loc=0, scale=1, size=500)
        y = np.random.normal(loc=0, scale=1, size=500)
        
        should_switch = should_switch_to_spearman(x, y, skewness_threshold=1.0)
        # With normal data and sufficient sample, should not switch
        assert should_switch is False

    def test_pearson_correlation_with_ci(self):
        """Test Pearson correlation with confidence interval."""
        np.random.seed(42)
        x = np.random.normal(loc=0, scale=1, size=100)
        y = 2 * x + np.random.normal(loc=0, scale=0.5, size=100)  # Strong positive correlation
        
        result = pearson_correlation_with_ci(x, y)
        
        assert "correlation_coefficient" in result
        assert "p_value" in result
        assert "confidence_interval" in result
        assert "method" in result
        assert result["method"] == "pearson"
        assert -1 <= result["correlation_coefficient"] <= 1
        assert len(result["confidence_interval"]) == 2

    def test_spearman_correlation_with_ci(self):
        """Test Spearman correlation with confidence interval."""
        np.random.seed(42)
        x = np.random.exponential(scale=1.0, size=100)
        y = 2 * x + np.random.exponential(scale=0.5, size=100)
        
        result = spearman_correlation_with_ci(x, y)
        
        assert "correlation_coefficient" in result
        assert "p_value" in result
        assert "confidence_interval" in result
        assert "method" in result
        assert result["method"] == "spearman"
        assert -1 <= result["correlation_coefficient"] <= 1
        assert len(result["confidence_interval"]) == 2

    def test_run_correlation_analysis_auto_switch(self):
        """Test run_correlation_analysis with auto-switch to Spearman."""
        # Create highly skewed data
        x = np.random.exponential(scale=1.0, size=500)
        y = np.random.exponential(scale=1.0, size=500)
        
        result = run_correlation_analysis(x, y)
        
        assert "method_used" in result
        assert result["method_used"] == "spearman"
        assert "adjusted_p_value" in result

    def test_run_correlation_analysis_pearson(self):
        """Test run_correlation_analysis with normal data (Pearson)."""
        np.random.seed(42)
        x = np.random.normal(loc=0, scale=1, size=500)
        y = np.random.normal(loc=0, scale=1, size=500)
        
        result = run_correlation_analysis(x, y)
        
        assert "method_used" in result
        assert result["method_used"] == "pearson"
        assert "adjusted_p_value" in result

class TestBenjaminiHochbergCorrection:
    """Test Benjamini-Hochberg FDR correction."""
    
    def test_apply_benjamini_hochberg_single_pvalue(self):
        """Test BH correction with a single p-value."""
        p_values = [0.05]
        adjusted = apply_benjamini_hochberg(p_values)
        
        assert len(adjusted) == 1
        # Single p-value should remain unchanged (n/n * p = p)
        assert adjusted[0] == 0.05

    def test_apply_benjamini_hochberg_multiple_pvalues(self):
        """Test BH correction with multiple p-values."""
        p_values = [0.01, 0.04, 0.06, 0.20]
        adjusted = apply_benjamini_hochberg(p_values)
        
        assert len(adjusted) == 4
        # Adjusted p-values should be >= original p-values
        for i, orig in enumerate(p_values):
            assert adjusted[i] >= orig

    def test_apply_benjamini_hochberg_monotonicity(self):
        """Test that BH-adjusted p-values maintain monotonicity."""
        # Create p-values that would violate monotonicity without correction
        p_values = [0.1, 0.05, 0.01]  # Decreasing order
        adjusted = apply_benjamini_hochberg(p_values)
        
        # After monotonicity correction, adjusted p-values should be non-decreasing
        # when sorted by original rank
        # This is a complex property, but we check that no adjusted p-value
        # is less than the previous one in the sorted order
        sorted_indices = np.argsort(p_values)
        sorted_adjusted = [adjusted[i] for i in sorted_indices]
        
        for i in range(1, len(sorted_adjusted)):
            assert sorted_adjusted[i] >= sorted_adjusted[i-1]

    def test_apply_benjamini_hochberg_empty_list(self):
        """Test BH correction with empty list."""
        p_values = []
        adjusted = apply_benjamini_hochberg(p_values)
        
        assert adjusted == []

    def test_apply_benjamini_hochberg_all_zeros(self):
        """Test BH correction with all zero p-values."""
        p_values = [0.0, 0.0, 0.0]
        adjusted = apply_benjamini_hochberg(p_values)
        
        assert all(p == 0.0 for p in adjusted)

    def test_apply_benjamini_hochberg_all_ones(self):
        """Test BH correction with all p-value = 1.0."""
        p_values = [1.0, 1.0, 1.0]
        adjusted = apply_benjamini_hochberg(p_values)
        
        assert all(p == 1.0 for p in adjusted)

class TestRunMultipleCorrelations:
    """Test running multiple correlations."""
    
    def test_run_multiple_correlations_basic(self):
        """Test running correlations on multiple variables."""
        np.random.seed(42)
        df = pd.DataFrame({
            "x1": np.random.normal(0, 1, 100),
            "x2": np.random.normal(0, 1, 100),
            "x3": np.random.normal(0, 1, 100),
            "y": np.random.normal(0, 1, 100)
        })
        
        results = run_multiple_correlations(df, ["x1", "x2", "x3"], "y")
        
        assert len(results) == 3
        for res in results:
            assert "variable_x" in res
            assert "variable_y" in res
            assert "correlation_coefficient" in res
            assert "adjusted_p_value" in res

    def test_run_multiple_correlations_missing_column(self):
        """Test handling of missing columns."""
        np.random.seed(42)
        df = pd.DataFrame({
            "x1": np.random.normal(0, 1, 100),
            "y": np.random.normal(0, 1, 100)
        })
        
        # Should skip non-existent column without error
        results = run_multiple_correlations(df, ["x1", "nonexistent"], "y")
        
        # Only x1 should be in results
        assert len(results) == 1
        assert results[0]["variable_x"] == "x1"

    def test_run_multiple_correlations_fdr_correction(self):
        """Test that FDR correction is applied across multiple tests."""
        np.random.seed(42)
        # Create data with known correlations
        df = pd.DataFrame({
            "x1": np.random.normal(0, 1, 200),
            "x2": np.random.normal(0, 1, 200),
            "y": np.random.normal(0, 1, 200)
        })
        
        results = run_multiple_correlations(df, ["x1", "x2"], "y")
        
        # Check that adjusted p-values are present
        for res in results:
            assert "adjusted_p_value" in res
            assert isinstance(res["adjusted_p_value"], float)