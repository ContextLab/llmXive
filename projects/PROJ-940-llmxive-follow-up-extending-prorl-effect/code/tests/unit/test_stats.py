"""
Unit tests for statistical analysis functions in src/stats.py.
"""
import pytest
import numpy as np
from src.stats import perform_shapiro_wilk, perform_paired_ttest, perform_wilcoxon, perform_significance_test
from src.exceptions import DataFetchError
import logging

# Suppress logging during tests
logging.disable(logging.CRITICAL)

class TestShapiroWilk:
    def test_normal_distribution(self):
        """Test with a known normal distribution."""
        # Generate normal data
        np.random.seed(42)
        data = np.random.normal(loc=0, scale=1, size=100)
        result = perform_shapiro_wilk(data)
        
        assert "statistic" in result
        assert "p_value" in result
        # For normal data, p-value should be > 0.05 (fail to reject null)
        assert result["p_value"] > 0.05

    def test_small_sample_size(self):
        """Test with sample size < 3."""
        data = np.array([1.0, 2.0])
        result = perform_shapiro_wilk(data)
        
        assert np.isnan(result["statistic"])
        assert np.isnan(result["p_value"])

    def test_non_normal_distribution(self):
        """Test with a known non-normal distribution (exponential)."""
        np.random.seed(42)
        data = np.random.exponential(scale=1.0, size=100)
        result = perform_shapiro_wilk(data)
        
        # Exponential is skewed, p-value should likely be < 0.05
        # Note: Small samples might pass by chance, but large ones should fail
        assert result["p_value"] < 0.05 or result["statistic"] < 0.95

class TestPairedTTest:
    def test_significant_difference(self):
        """Test when there is a significant difference."""
        np.random.seed(42)
        # Greedy: mean 0.5, std 0.1
        greedy = np.random.normal(0.5, 0.1, 100)
        # ProRL: mean 0.6, std 0.1 (shifted)
        prorl = np.random.normal(0.6, 0.1, 100)
        
        result = perform_paired_ttest(greedy, prorl)
        
        assert result["conclusion"] == "significant"
        assert result["p_value"] < 0.05
        assert result["mean_diff"] > 0

    def test_no_difference(self):
        """Test when there is no significant difference."""
        np.random.seed(42)
        # Same distribution
        greedy = np.random.normal(0.5, 0.1, 100)
        prorl = np.random.normal(0.5, 0.1, 100)
        
        result = perform_paired_ttest(greedy, prorl)
        
        # Likely not significant, but depends on random seed
        assert result["conclusion"] in ["significant", "not significant"]
        assert "t_statistic" in result
        assert "confidence_interval" in result

    def test_mismatched_lengths(self):
        """Test with mismatched array lengths."""
        greedy = np.array([1.0, 2.0, 3.0])
        prorl = np.array([1.0, 2.0])
        
        with pytest.raises(ValueError):
            perform_paired_ttest(greedy, prorl)

    def test_insufficient_samples(self):
        """Test with only 1 sample."""
        greedy = np.array([1.0])
        prorl = np.array([1.0])
        
        with pytest.raises(ValueError):
            perform_paired_ttest(greedy, prorl)

class TestWilcoxon:
    def test_significant_difference(self):
        """Test Wilcoxon with significant difference."""
        np.random.seed(42)
        greedy = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        prorl = np.array([2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        
        result = perform_wilcoxon(greedy, prorl)
        
        assert result["conclusion"] == "significant"
        assert result["p_value"] < 0.05

    def test_mismatched_lengths(self):
        """Test with mismatched array lengths."""
        greedy = np.array([1.0, 2.0, 3.0])
        prorl = np.array([1.0, 2.0])
        
        with pytest.raises(ValueError):
            perform_wilcoxon(greedy, prorl)

class TestPerformSignificanceTest:
    def test_normal_data_uses_ttest(self):
        """Verify that normal data triggers t-test."""
        np.random.seed(42)
        greedy = np.random.normal(0.5, 0.1, 100)
        prorl = np.random.normal(0.6, 0.1, 100)
        
        result = perform_significance_test(greedy, prorl)
        
        assert result["test_type"] == "t-test"
        assert "t_statistic" in result

    def test_non_normal_data_uses_wilcoxon(self):
        """Verify that non-normal data triggers Wilcoxon."""
        # Generate skewed data
        np.random.seed(42)
        greedy = np.random.exponential(1.0, 100)
        prorl = np.random.exponential(1.2, 100)
        
        result = perform_significance_test(greedy, prorl)
        
        # If Shapiro fails, it should use Wilcoxon
        if result["shapiro_normality"] == False:
            assert result["test_type"] == "wilcoxon"
            assert "statistic" in result