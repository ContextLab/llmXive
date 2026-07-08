"""
test_metrics.py

Tests for metrics.py functions.
"""
import os
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from src.metrics import (
    calculate_pearson_correlation_all_genes,
    calculate_stability_metrics,
    compare_parametric_empirical_pvalues,
    calculate_pvalue_inflation,
    generate_bland_altman_plot,
    apply_benjamini_hochberg_correction
)


def test_pearson_correlation_all_genes_basic():
    """Test basic Pearson correlation calculation."""
    # Create synthetic data with known correlation
    np.random.seed(42)
    n_genes = 1000
    full_log2fc = pd.Series(np.random.randn(n_genes), index=[f'gene_{i}' for i in range(n_genes)])
    subset_log2fc = full_log2fc * 0.9 + np.random.randn(n_genes) * 0.1  # High correlation

    corr, p_val = calculate_pearson_correlation_all_genes(full_log2fc, subset_log2fc)

    assert 0.8 < corr < 1.0, f"Expected high correlation, got {corr}"
    assert p_val < 0.05, f"Expected significant p-value, got {p_val}"


def test_pearson_correlation_all_genes_no_overlap():
    """Test correlation with no overlapping genes."""
    full_log2fc = pd.Series([1, 2, 3], index=['gene_a', 'gene_b', 'gene_c'])
    subset_log2fc = pd.Series([1, 2, 3], index=['gene_x', 'gene_y', 'gene_z'])

    with pytest.raises(ValueError, match="No common genes"):
        calculate_pearson_correlation_all_genes(full_log2fc, subset_log2fc)


def test_pearson_correlation_all_genes_insufficient_data():
    """Test correlation with insufficient data points."""
    full_log2fc = pd.Series([1.0, np.nan], index=['gene_a', 'gene_b'])
    subset_log2fc = pd.Series([1.0, np.nan], index=['gene_a', 'gene_b'])

    corr, p_val = calculate_pearson_correlation_all_genes(full_log2fc, subset_log2fc)

    assert np.isnan(corr), f"Expected NaN correlation, got {corr}"
    assert np.isnan(p_val), f"Expected NaN p-value, got {p_val}"


def test_calculate_stability_metrics():
    """Test stability metrics calculation across multiple subsets."""
    np.random.seed(42)
    n_genes = 500
    gene_ids = [f'gene_{i}' for i in range(n_genes)]

    full_log2fc = pd.Series(np.random.randn(n_genes), index=gene_ids)

    # Create 3 subsets with varying correlations
    subset1 = full_log2fc * 0.95 + np.random.randn(n_genes) * 0.05
    subset2 = full_log2fc * 0.85 + np.random.randn(n_genes) * 0.15
    subset3 = full_log2fc * 0.70 + np.random.randn(n_genes) * 0.30

    df = calculate_stability_metrics(full_log2fc, [subset1, subset2, subset3])

    assert len(df) == 3
    assert 'correlation' in df.columns
    assert 'p_value' in df.columns
    assert 'n_genes' in df.columns

    # Check that correlations decrease as expected
    assert df.iloc[0]['correlation'] > df.iloc[1]['correlation'] > df.iloc[2]['correlation']


def test_compare_parametric_empirical_pvalues_ks():
    """Test KS test comparison of p-values."""
    # Generate uniform p-values (ideal case)
    np.random.seed(42)
    n = 1000
    parametric_pvals = np.random.uniform(0, 1, n)
    empirical_pvals = np.random.uniform(0, 1, n)

    result = compare_parametric_empirical_pvalues(parametric_pvals, empirical_pvals, method='ks')

    assert 'ks_statistic' in result
    assert 'ks_p_value' in result
    assert 'pass_uniformity' in result
    assert result['pass_uniformity'] == True  # Uniform distributions should pass


def test_compare_parametric_empirical_pvalues_non_uniform():
    """Test KS test with non-uniform p-values."""
    # Generate skewed p-values
    np.random.seed(42)
    n = 1000
    parametric_pvals = np.random.beta(0.5, 5, n)  # Skewed towards 0
    empirical_pvals = np.random.beta(0.5, 5, n)

    result = compare_parametric_empirical_pvalues(parametric_pvals, empirical_pvals, method='ks')

    # Non-uniform distributions may or may not pass depending on the skew
    assert 'ks_statistic' in result
    assert 'ks_p_value' in result


def test_calculate_pvalue_inflation():
    """Test p-value inflation calculation."""
    np.random.seed(42)
    n = 500
    parametric_pvals = np.random.uniform(0, 1, n)
    empirical_pvals = parametric_pvals * 1.1  # Slight inflation

    result = calculate_pvalue_inflation(parametric_pvals, empirical_pvals)

    assert 'mad' in result
    assert 'median_diff' in result
    assert 'mean_diff' in result


def test_apply_benjamini_hochberg_correction():
    """Test BH FDR correction."""
    np.random.seed(42)
    p_values = np.array([0.01, 0.03, 0.02, 0.05, 0.04, 0.10, 0.15, 0.20])

    adjusted = apply_benjamini_hochberg_correction(p_values)

    assert len(adjusted) == len(p_values)
    assert all(0 <= adjusted) and all(adjusted <= 1)
    # Adjusted p-values should be >= original p-values
    assert all(adjusted >= p_values - 1e-10)


def test_generate_bland_altman_plot():
    """Test Bland-Altman plot generation."""
    np.random.seed(42)
    n = 100
    parametric_pvals = np.random.uniform(0, 1, n)
    empirical_pvals = np.random.uniform(0, 1, n)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test_bland_altman.png'
        result_path = generate_bland_altman_plot(
            parametric_pvals,
            empirical_pvals,
            output_path=output_path
        )

        assert result_path.exists()
        assert result_path.suffix == '.png'


def test_generate_bland_altman_plot_no_valid_data():
    """Test Bland-Altman plot with no valid data."""
    parametric_pvals = np.array([np.nan, np.nan])
    empirical_pvals = np.array([np.nan, np.nan])

    with pytest.raises(ValueError, match="No valid p-values"):
        generate_bland_altman_plot(parametric_pvals, empirical_pvals)


class TestPearsonCorrelationAllGenes:
    """Test class for Pearson correlation on all genes."""

    def test_high_correlation_scenario(self):
        """Test scenario with high correlation between full and subset."""
        np.random.seed(123)
        n = 2000
        full = pd.Series(np.random.randn(n), index=[f'g{i}' for i in range(n)])
        subset = full * 0.98 + np.random.randn(n) * 0.02

        corr, p_val = calculate_pearson_correlation_all_genes(full, subset)

        assert corr > 0.95
        assert p_val < 1e-10

    def test_low_correlation_scenario(self):
        """Test scenario with low correlation."""
        np.random.seed(456)
        n = 1000
        full = pd.Series(np.random.randn(n), index=[f'g{i}' for i in range(n)])
        subset = pd.Series(np.random.randn(n), index=[f'g{i}' for i in range(n)])

        corr, p_val = calculate_pearson_correlation_all_genes(full, subset)

        # With random data, correlation should be near 0
        assert -0.2 < corr < 0.2