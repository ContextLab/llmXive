import pytest
import pandas as pd
import numpy as np
from code.utils.stats import (
    run_statistical_analysis, 
    run_domain_stratified_analysis, 
    fit_linear_mixed_model,
    run_paired_ttest
)

@pytest.fixture
def sample_data():
    """Create a synthetic dataset with multiple domains and methods."""
    np.random.seed(42)
    n_samples = 100
    data = []
    domains = ["Medical", "Office", "Education"]
    methods = ["Gatekeeper", "Baseline"]
    
    for domain in domains:
        for method in methods:
            # Generate scores with slight variation per domain/method
            base_score = 0.5 if method == "Gatekeeper" else 0.6
            scores = np.random.normal(base_score, 0.1, size=20)
            for score in scores:
                data.append({
                    "Domain": domain,
                    "method": method,
                    "score": score
                })
                
    return pd.DataFrame(data)

def test_stratified_analysis_per_domain(sample_data):
    """Test that stratified analysis runs separately for each domain."""
    result = run_domain_stratified_analysis(sample_data)
    
    assert "per_domain_results" in result
    assert "summary" in result
    
    domains = sample_data["Domain"].unique()
    for domain in domains:
        assert domain in result["per_domain_results"]
        
    assert result["summary"]["total_domains"] == len(domains)
    assert result["summary"]["domains_analyzed"] <= len(domans)

def test_fallback_on_singular_matrix(sample_data):
    """Test that the system falls back to paired tests when LMM fails."""
    # Artificially create a singular matrix scenario by making data flat in one domain
    flat_data = sample_data.copy()
    flat_data.loc[flat_data["Domain"] == "Medical", "score"] = 0.5  # No variance
    
    result = run_statistical_analysis(flat_data)
    
    # LMM might fail or succeed depending on statsmodels behavior with flat data
    # The key is that the pipeline should not crash and should provide a fallback
    assert "lmm_full" in result
    assert "fallback" in result or result["lmm_full"]["success"]
    
    # If LMM failed, fallback must be present and successful
    if not result["lmm_full"]["success"]:
        assert result["fallback"] is not None
        assert result["fallback"]["success"]

def test_paired_ttest_execution(sample_data):
    """Test that paired t-test runs correctly on a subset."""
    subset = sample_data[sample_data["Domain"] == "Medical"]
    result = run_paired_ttest(subset)
    
    assert "success" in result
    assert result["success"]
    assert "statistic" in result
    assert "pvalue" in result
    assert result["n"] == len(subset) // 2  # Assuming equal split

def test_full_pipeline_integration(sample_data):
    """Test the full statistical analysis pipeline."""
    result = run_statistical_analysis(sample_data)
    
    assert "data_summary" in result
    assert result["data_summary"]["n_total"] == len(sample_data)
    assert result["data_summary"]["n_domains"] == 3
    assert set(result["data_summary"]["methods"]) == {"Gatekeeper", "Baseline"}
    
    # Check stratified results structure
    assert "per_domain_results" in result["stratified"]
    assert "summary" in result["stratified"]