"""
Contract tests for statistical analysis output schema.

Verifies that the output of run_statistical_analysis matches the expected structure.
"""

import pytest
import pandas as pd
import numpy as np
from code.utils.stats import (
    shapiro_wilk_test,
    fit_linear_mixed_model,
    run_paired_ttest,
    run_wilcoxon_test,
    run_statistical_analysis,
    run_domain_stratified_analysis
)

def test_shapiro_wilk_output_structure():
    """Test that Shapiro-Wilk returns expected keys."""
    data = np.random.normal(0, 1, 100)
    result = shapiro_wilk_test(data)
    
    assert "statistic" in result
    assert "pvalue" in result
    assert isinstance(result["statistic"], float)
    assert isinstance(result["pvalue"], float)

def test_lmm_output_structure():
    """Test that LMM returns expected keys on success."""
    df = pd.DataFrame({
        "score": np.random.normal(5, 1, 100),
        "method": np.random.choice(["A", "B"], 100),
        "Domain": np.random.choice(["X", "Y"], 100)
    })
    
    result = fit_linear_mixed_model(df)
    
    assert "success" in result
    assert "method_used" in result
    assert result["method_used"] == "LMM"
    
    if result["success"]:
        assert "statistic" in result
        assert "pvalue" in result
        assert "coefficients" in result

def test_paired_ttest_output_structure():
    """Test that paired t-test returns expected keys."""
    g1 = np.random.normal(0, 1, 50)
    g2 = np.random.normal(0.5, 1, 50)
    
    result = run_paired_ttest(g1, g2)
    
    assert "statistic" in result
    assert "pvalue" in result

def test_wilcoxon_output_structure():
    """Test that Wilcoxon returns expected keys."""
    g1 = np.random.normal(0, 1, 50)
    g2 = np.random.normal(0.5, 1, 50)
    
    result = run_wilcoxon_test(g1, g2)
    
    assert "statistic" in result
    assert "pvalue" in result

def test_full_analysis_output_structure():
    """Test that full statistical analysis returns expected structure."""
    np.random.seed(42)
    df = pd.DataFrame({
        "score": np.concatenate([
            np.random.normal(5, 1, 50),
            np.random.normal(5.5, 1, 50)
        ]),
        "method": ["Gatekeeper"] * 50 + ["Baseline"] * 50,
        "Domain": np.random.choice(["medical", "office"], 100)
    })
    
    result = run_statistical_analysis(df)
    
    # Check top-level keys
    assert "success" in result
    assert "method_used" in result
    assert "statistic" in result
    assert "pvalue" in result
    
    # Check normality check structure
    assert "normality_check" in result
    assert isinstance(result["normality_check"], dict)

def test_domain_stratified_output_structure():
    """Test that domain-stratified analysis returns expected structure."""
    np.random.seed(42)
    df = pd.DataFrame({
        "score": np.random.normal(5, 1, 200),
        "method": np.random.choice(["Gatekeeper", "Baseline"], 200),
        "Domain": np.random.choice(["medical", "office", "education"], 200)
    })
    
    result = run_domain_stratified_analysis(df)
    
    assert isinstance(result, dict)
    # Each domain should have a result dict
    for domain, res in result.items():
        assert isinstance(res, dict)
        assert "success" in res or "error" in res
