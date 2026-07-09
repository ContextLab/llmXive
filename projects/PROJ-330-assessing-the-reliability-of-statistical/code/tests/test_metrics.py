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
    apply_benjamini_hochberg_correction,
    generate_bland_altman_plot
)

def test_pearson_correlation_all_genes_basic():
    full = pd.Series([1, 2, 3, 4, 5], index=['a', 'b', 'c', 'd', 'e'])
    subset = pd.Series([1.1, 2.1, 2.9, 4.1, 5.1], index=['a', 'b', 'c', 'd', 'e'])
    corr = calculate_pearson_correlation_all_genes(full, subset)
    assert 0.9 < corr <= 1.0

def test_pearson_correlation_all_genes_no_overlap():
    full = pd.Series([1, 2], index=['a', 'b'])
    subset = pd.Series([1, 2], index=['c', 'd'])
    corr = calculate_pearson_correlation_all_genes(full, subset)
    assert np.isnan(corr)

def test_pearson_correlation_all_genes_insufficient_data():
    full = pd.Series([1], index=['a'])
    subset = pd.Series([1], index=['a'])
    corr = calculate_pearson_correlation_all_genes(full, subset)
    assert np.isnan(corr)

def test_calculate_stability_metrics():
    full = pd.Series([1, 2, 3, 4, 5], index=['a', 'b', 'c', 'd', 'e'])
    subsets = [
        pd.Series([1.1, 2.1, 2.9, 4.1, 5.1], index=['a', 'b', 'c', 'd', 'e']),
        pd.Series([1.2, 2.2, 2.8, 4.2, 5.2], index=['a', 'b', 'c', 'd', 'e'])
    ]
    metrics = calculate_stability_metrics(full, subsets)
    assert "mean_correlation" in metrics
    assert "std_correlation" in metrics

def test_compare_parametric_empirical_pvalues_ks():
    """
    T020: Test KS statistic uniform distribution passes.
    When parametric and empirical p-values are both uniform, the KS test
    should fail to reject the null hypothesis (p-value > 0.05).
    """
    # Generate two sets of uniform p-values (simulating perfect agreement)
    np.random.seed(42)
    p1 = np.random.uniform(0, 1, 2000)
    p2 = np.random.uniform(0, 1, 2000)
    
    result = compare_parametric_empirical_pvalues(p1, p2)
    
    assert "ks_statistic" in result
    assert "ks_pvalue" in result
    # The KS statistic should be small for uniform distributions
    assert result["ks_statistic"] < 0.1
    # The p-value should be > 0.05 (fail to reject null hypothesis of uniformity)
    assert result["ks_pvalue"] > 0.05

def test_compare_parametric_empirical_pvalues_non_uniform():
    """
    T020: Test that non-uniform distributions are detected.
    When empirical p-values are bimodal (inflation), the KS test should reject.
    """
    np.random.seed(42)
    p1 = np.random.uniform(0, 1, 2000)
    # Create a bimodal distribution representing p-value inflation
    p2 = np.array([0.01] * 1000 + [0.99] * 1000)
    
    result = compare_parametric_empirical_pvalues(p1, p2)
    
    # The KS statistic should be large for bimodal distributions
    assert result["ks_statistic"] > 0.4
    # The p-value should be < 0.05 (reject null hypothesis)
    assert result["ks_pvalue"] < 0.05

def test_calculate_pvalue_inflation():
    p1 = np.array([0.1, 0.2, 0.3])
    p2 = np.array([0.15, 0.25, 0.35])
    inflation = calculate_pvalue_inflation(p1, p2)
    assert inflation == 0.05

def test_apply_benjamini_hochberg_correction():
    p = np.array([0.01, 0.04, 0.03, 0.20])
    corrected = apply_benjamini_hochberg_correction(p)
    assert len(corrected) == len(p)
    assert all(0 <= c <= 1 for c in corrected)

def test_generate_bland_altman_plot():
    """
    T020: Test Bland-Altman plot generation.
    Verifies that the function creates a valid plot file and returns the path.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "bland_altman_test.png"
        
        # Generate sample p-values (parametric vs empirical)
        np.random.seed(42)
        p1 = np.random.uniform(0, 1, 100)
        p2 = p1 + np.random.normal(0, 0.05, 100)  # Add small noise
        
        result_path = generate_bland_altman_plot(p1, p2, output_path)
        
        # Verify the file was created
        assert result_path.exists(), f"Plot file not created at {result_path}"
        assert result_path.suffix == ".png", f"Expected .png file, got {result_path.suffix}"
        
        # Verify file has non-zero size
        assert result_path.stat().st_size > 0, "Plot file is empty"

class TestPearsonCorrelationAllGenes:
    pass