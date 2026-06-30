"""
Unit tests for statistical_tests.py module.
"""

import pytest
import numpy as np
from src.evaluation.statistical_tests import (
    paired_ttest,
    wilcoxon_effect_size,
    bootstrap_ci,
    run_full_statistical_analysis
)

class TestStatisticalTests:
    """Tests for statistical analysis functions."""

    def test_paired_ttest_basic(self):
        """Test basic paired t-test functionality."""
        np.random.seed(42)
        a = np.random.normal(0.75, 0.05, 50)
        b = np.random.normal(0.80, 0.05, 50)

        result = paired_ttest(a, b, alpha=0.05)

        assert "statistic" in result
        assert "pvalue" in result
        assert "significant" in result
        assert "mean_diff" in result
        assert isinstance(result["statistic"], float)
        assert isinstance(result["pvalue"], float)
        assert result["n_samples"] == 50

    def test_paired_ttest_identical(self):
        """Test paired t-test with identical arrays (should yield p=1.0)."""
        data = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        result = paired_ttest(data, data, alpha=0.05)

        assert result["pvalue"] == 1.0
        assert result["statistic"] == 0.0
        assert not result["significant"]

    def test_paired_ttest_invalid_shape(self):
        """Test paired t-test with mismatched shapes."""
        a = [1, 2, 3]
        b = [1, 2]
        with pytest.raises(ValueError):
            paired_ttest(a, b)

    def test_paired_ttest_empty(self):
        """Test paired t-test with empty arrays."""
        with pytest.raises(ValueError):
            paired_ttest([], [])

    def test_wilcoxon_effect_size_basic(self):
        """Test Wilcoxon effect size calculation."""
        np.random.seed(42)
        a = np.random.normal(0.75, 0.05, 50)
        b = np.random.normal(0.80, 0.05, 50)

        result = wilcoxon_effect_size(a, b)

        assert "statistic" in result
        assert "pvalue" in result
        assert "effect_size" in result
        assert "ci_lower" in result
        assert "ci_upper" in result
        assert "z_statistic" in result
        assert "formula" in result
        assert result["formula"] == "r = Z / sqrt(N)"

    def test_wilcoxon_effect_size_identical(self):
        """Test Wilcoxon with identical arrays."""
        data = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        result = wilcoxon_effect_size(data, data)

        # Effect size should be 0 for identical data
        assert abs(result["effect_size"]) < 1e-6
        assert result["pvalue"] == 1.0

    def test_bootstrap_ci_basic(self):
        """Test bootstrap CI calculation."""
        np.random.seed(42)
        values = np.random.normal(0.8, 0.1, 100)

        result = bootstrap_ci(values, n_resamples=100, confidence=0.95)

        assert "mean" in result
        assert "ci_lower" in result
        assert "ci_upper" in result
        assert result["n_resamples"] == 100
        assert result["confidence"] == 0.95
        assert result["ci_lower"] <= result["mean"] <= result["ci_upper"]

    def test_bootstrap_ci_empty(self):
        """Test bootstrap CI with empty array."""
        with pytest.raises(ValueError):
            bootstrap_ci([])

    def test_full_analysis(self):
        """Test the full analysis pipeline."""
        np.random.seed(42)
        a = np.random.normal(0.75, 0.05, 50)
        b = np.random.normal(0.80, 0.05, 50)

        results = run_full_statistical_analysis(a, b)

        assert "paired_ttest" in results
        assert "wilcoxon" in results
        assert "bootstrap_ci" in results
        assert "config" in results
        assert results["config"]["primary_outcome"] == "Wilcoxon effect size (r) with 95% CI"
        assert results["config"]["alpha"] == 0.05
        assert results["config"]["bootstrap_resamples"] == 1000

    def test_wilcoxon_small_sample(self):
        """Test Wilcoxon with small sample size (edge case)."""
        a = np.array([1, 2, 3, 4, 5])
        b = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        # Should not raise an error, just a warning
        result = wilcoxon_effect_size(a, b)
        assert "effect_size" in result
        assert "ci_lower" in result
        assert "ci_upper" in result