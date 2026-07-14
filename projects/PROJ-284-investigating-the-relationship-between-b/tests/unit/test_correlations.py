"""
Unit tests for correlation and PCA logic.
"""
import pytest
import pandas as pd
import numpy as np
from code.analysis.correlations import (
    perform_pca_on_metrics,
    run_correlations_with_fd_covariate,
    apply_fdr_correction,
    generate_full_metrics
)

def test_pca_on_metrics():
    """Test PCA computation on synthetic data."""
    data = {
        "subject_id": [1, 2, 3, 4, 5],
        "modularity": [0.1, 0.2, 0.3, 0.4, 0.5],
        "efficiency": [0.8, 0.7, 0.6, 0.5, 0.4],
        "participation": [0.3, 0.4, 0.5, 0.6, 0.7]
    }
    df = pd.DataFrame(data)
    
    loadings, scores = perform_pca_on_metrics(df, ["modularity", "efficiency", "participation"])
    
    assert not loadings.empty
    assert not scores.empty
    assert "subject_id" in scores.columns
    assert "pca_factor_1" in scores.columns
    assert "pca_factor_2" in scores.columns

def test_correlation_with_fd():
    """Test partial correlation with FD covariate."""
    np.random.seed(42)
    n = 50
    data = {
        "subject_id": range(n),
        "metric": np.random.rand(n),
        "motor_score": np.random.rand(n),
        "fd": np.random.rand(n)
    }
    df = pd.DataFrame(data)
    
    results = run_correlations_with_fd_covariate(df, ["metric"], "motor_score", "fd")
    
    assert not results.empty
    assert "r" in results.columns
    assert "p" in results.columns
    assert "significant" in results.columns

def test_fdr_correction():
    """Test Benjamini-Hochberg FDR correction."""
    data = {
        "metric": ["m1", "m2", "m3", "m4"],
        "p": [0.01, 0.04, 0.03, 0.005]
    }
    df = pd.DataFrame(data)
    
    corrected = apply_fdr_correction(df, "p", alpha=0.05)
    
    assert "q" in corrected.columns
    assert "significant_fdr" in corrected.columns
    # Check monotonicity of q-values (conceptually)
    assert all(corrected["q"] >= 0) and all(corrected["q"] <= 1)

def test_generate_full_metrics():
    """Test merging metrics and PCA scores."""
    metrics = pd.DataFrame({
        "subject_id": [1, 2, 3],
        "m1": [0.1, 0.2, 0.3],
        "m2": [0.4, 0.5, 0.6]
    })
    scores = pd.DataFrame({
        "subject_id": [1, 2, 3],
        "pca_factor_1": [0.9, 0.8, 0.7]
    })
    
    merged = generate_full_metrics(metrics, scores)
    
    assert not merged.empty
    assert "m1" in merged.columns
    assert "m2" in merged.columns
    assert "pca_factor_1" in merged.columns
    assert len(merged) == 3