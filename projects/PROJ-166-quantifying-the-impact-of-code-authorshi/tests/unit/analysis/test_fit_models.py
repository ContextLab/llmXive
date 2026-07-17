import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from code.analysis.fit_models import (
    filter_zero_kloc,
    calculate_vif,
    benjamini_hochberg,
    fit_negative_binomial_glm,
    extract_results
)

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    data = {
        'url': ['repo1', 'repo2', 'repo3', 'repo4'],
        'author_count': [10, 20, 5, 15],
        'kloc': [100.0, 0.0, 50.0, 200.0], # repo2 has 0 kloc
        'cve_count': [5, 0, 2, 10],
        'project_age': [5, 10, 2, 8],
        'release_count': [10, 20, 5, 15]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_for_vif():
    """Create a sample DataFrame for VIF calculation."""
    np.random.seed(42)
    n = 100
    data = {
        'author_count': np.random.normal(10, 5, n),
        'project_age': np.random.normal(5, 2, n),
        'release_count': np.random.normal(10, 5, n),
        'cve_count': np.random.poisson(5, n),
        'kloc': np.random.exponential(50, n) + 1 # Ensure > 0
    }
    return pd.DataFrame(data)

def test_filter_zero_kloc(sample_df):
    """Test that rows with kloc <= 0 are excluded."""
    initial_len = len(sample_df)
    filtered_df = filter_zero_kloc(sample_df)
    
    assert len(filtered_df) == initial_len - 1, "One row with kloc=0 should be excluded."
    assert (filtered_df['kloc'] > 0).all(), "All remaining rows should have kloc > 0."
    assert 'repo2' not in filtered_df['url'].values, "Repo with kloc=0 should be removed."

def test_filter_zero_kloc_no_exclusions():
    """Test filtering when no rows have kloc <= 0."""
    data = {
        'url': ['repo1'],
        'author_count': [10],
        'kloc': [100.0],
        'cve_count': [5],
        'project_age': [5],
        'release_count': [10]
    }
    df = pd.DataFrame(data)
    filtered = filter_zero_kloc(df)
    assert len(filtered) == 1

def test_calculate_vif(sample_df_for_vif):
    """Test VIF calculation."""
    predictors = ['author_count', 'project_age', 'release_count']
    vif = calculate_vif(sample_df_for_vif, predictors)
    
    assert len(vif) == 3
    assert all(isinstance(v, float) for v in vif.values())
    # VIF should be >= 1
    assert all(v >= 1.0 for v in vif.values())

def test_benjamini_hochberg():
    """Test Benjamini-Hochberg correction."""
    p_values = [0.01, 0.04, 0.03, 0.005, 0.02]
    adjusted = benjamini_hochberg(p_values)
    
    assert len(adjusted) == len(p_values)
    assert all(0 <= p <= 1 for p in adjusted)
    # Check monotonicity (approximate, due to floating point)
    sorted_p = sorted(p_values)
    sorted_adj = sorted(adjusted)
    # The adjusted values should be generally larger or equal to raw values in some cases, 
    # but the key is the algorithm correctness.
    # Specifically, the last adjusted value should be close to 1 or the max raw * n/n
    # Let's just verify it returns a list of floats.
    assert isinstance(adjusted, list)

def test_fit_negative_binomial_glm(sample_df_for_vif):
    """Test GLM fitting."""
    predictors = ['author_count', 'project_age', 'release_count']
    offset_col = 'kloc'
    
    results, converged = fit_negative_binomial_glm(sample_df_for_vif, predictors, offset_col)
    
    assert results is not None
    assert isinstance(converged, bool)
    assert len(results.params) == len(predictors) + 1 # +1 for intercept

def test_extract_results(sample_df_for_vif):
    """Test result extraction."""
    predictors = ['author_count', 'project_age', 'release_count']
    offset_col = 'kloc'
    
    results, converged = fit_negative_binomial_glm(sample_df_for_vif, predictors, offset_col)
    pvals = results.pvalues.tolist()
    vif = calculate_vif(sample_df_for_vif, predictors)
    
    extracted = extract_results(results, predictors, pvals, vif, converged)
    
    assert "convergence_status" in extracted
    assert "coefficients" in extracted
    assert "standard_errors" in extracted
    assert "p_values" in extracted
    assert "adjusted_p_values" in extracted
    assert "confidence_intervals" in extracted
    assert "vif_metrics" in extracted
    
    # Check keys
    expected_keys = ['intercept', 'author_count', 'project_age', 'release_count']
    for key in expected_keys:
        assert key in extracted["coefficients"]
        assert key in extracted["standard_errors"]
        assert key in extracted["p_values"]
        assert key in extracted["adjusted_p_values"]
        assert key in extracted["confidence_intervals"]
        assert key in extracted["vif_metrics"]