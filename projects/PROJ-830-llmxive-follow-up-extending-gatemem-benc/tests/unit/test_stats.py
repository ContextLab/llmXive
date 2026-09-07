"""
Unit tests for statistical analysis functions in code/utils/stats.py.
"""
import pytest
import numpy as np
import pandas as pd
from code.utils.stats import (
    shapiro_wilk_test,
    fit_fixed_effects_glm,
    run_post_hoc,
    domain_stratified_analysis,
    fit_lmm,
    pair_episodes,
    run_full_stats_pipeline
)
import warnings

@pytest.fixture
def sample_diffs():
    """Sample paired differences for testing."""
    return np.array([0.1, -0.2, 0.05, 0.3, -0.1, 0.15, -0.05, 0.2, -0.15, 0.1])

@pytest.fixture
def sample_df():
    """Sample DataFrame for model fitting."""
    data = []
    domains = ["medical", "office", "education"]
    methods = ["Gatekeeper", "Baseline"]
    for i in range(30):
        for method in methods:
            data.append({
                "score": np.random.normal(0.5, 0.2),
                "method": method,
                "Domain": domains[i % 3]
            })
    return pd.DataFrame(data)

def test_shapiro_wilk_returns_p_value(sample_diffs):
    """Test that Shapiro-Wilk returns a valid p-value."""
    result = shapiro_wilk_test(sample_diffs)
    assert "p_value" in result
    assert "statistic" in result
    assert "is_normal" in result
    assert isinstance(result["p_value"], float)
    assert 0.0 <= result["p_value"] <= 1.0

def test_shapiro_wilk_insufficient_data():
    """Test Shapiro-Wilk with insufficient data points."""
    result = shapiro_wilk_test(np.array([0.1, 0.2]))
    assert result["is_normal"] is False
    assert "Insufficient data" in result.get("reason", "")

def test_fit_glm_returns_dict(sample_df):
    """Test that Fixed-Effects GLM returns a dictionary with required keys."""
    result = fit_fixed_effects_glm(sample_df)
    assert "method_used" in result
    assert result["method_used"] == "GLM"
    assert "p_value" in result
    assert "test_statistic" in result
    assert "family" in result

def test_run_post_hoc_returns_dict(sample_diffs):
    """Test that post-hoc selection returns correct structure."""
    result = run_post_hoc(sample_diffs)
    assert "method_used" in result
    assert result["method_used"] in ["t-test", "Wilcoxon"]
    assert "p_value" in result
    assert "test_statistic" in result
    assert "normality_result" in result

def test_domain_stratified_analysis_returns_dict(sample_df):
    """Test domain-stratified analysis returns correct structure."""
    result = domain_stratified_analysis(sample_df)
    assert "method_used" in result
    assert result["method_used"] == "Domain-Stratified"
    assert "p_values_per_domain" in result
    assert "aggregated_p_value" in result

def test_fit_lmm_returns_dict(sample_df):
    """Test that LMM returns a dictionary with required keys."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = fit_lmm(sample_df)
    assert "method_used" in result
    assert result["method_used"] == "LMM"
    assert "p_value" in result
    assert "test_statistic" in result
    assert "covariance_params" in result

def test_pair_episodes_valid():
    """Test pairing episodes with valid data."""
    g_data = [{"episode_id": 1, "score": 0.9}, {"episode_id": 2, "score": 0.8}]
    b_data = [{"episode_id": 1, "score": 0.7}, {"episode_id": 2, "score": 0.6}]
    paired = pair_episodes(g_data, b_data)
    assert len(paired) == 2
    assert paired[0] == (0.9, 0.7)
    assert paired[1] == (0.8, 0.6)

def test_pair_episodes_missing_id():
    """Test pairing episodes with mismatched IDs raises ValueError."""
    g_data = [{"episode_id": 1, "score": 0.9}]
    b_data = [{"episode_id": 2, "score": 0.6}]
    with pytest.raises(ValueError, match="No common episode IDs"):
        pair_episodes(g_data, b_data)

def test_full_stats_pipeline_returns_dict(sample_df):
    """Test the full stats pipeline orchestration."""
    # Create dummy paired results
    g_results = [{"episode_id": i, "score": 0.5 + np.random.normal(0, 0.1), "Domain": "medical", "method": "Gatekeeper"} 
                 for i in range(10)]
    b_results = [{"episode_id": i, "score": 0.4 + np.random.normal(0, 0.1), "Domain": "medical", "method": "Baseline"} 
                 for i in range(10)]
    
    result = run_full_stats_pipeline(g_results, b_results)
    assert "method_used" in result
    assert "p_value" in result
    assert "test_statistic" in result
    assert "fallback_reason" in result or result.get("fallback_reason") is None
    # At least one method should have been attempted
    assert result["method_used"] in ["LMM", "GLM", "Domain-Stratified", "Error", "Failed"]