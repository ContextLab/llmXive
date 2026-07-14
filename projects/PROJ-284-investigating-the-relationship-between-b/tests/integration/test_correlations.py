"""
Integration test for T023a, T023b, T024, T025.
Verifies synthetic data correlation analysis pipeline.
"""
import os
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

from code.analysis.correlations import (
    perform_pca_on_metrics,
    generate_full_metrics,
    run_correlations_with_fd_covariate,
    apply_fdr_correction,
    save_pca_results,
    save_correlation_results,
    save_full_metrics
)

@pytest.fixture
def synthetic_metrics_data():
    """Generates a synthetic dataset with known correlations."""
    np.random.seed(42)
    n = 100
    data = {
        "subject_id": [f"sub_{i:03d}" for i in range(n)],
        "modularity": np.random.rand(n),
        "global_efficiency": np.random.rand(n),
        "participation_coef": np.random.rand(n),
        "within_module_degree": np.random.rand(n),
        "MeanFD": np.random.rand(n) * 0.5, # Low motion
        "motor_score": np.random.rand(n)
    }
    # Inject a known correlation: modularity vs motor_score
    data["motor_score"] = data["modularity"] * 0.8 + np.random.normal(0, 0.1, n)
    
    return pd.DataFrame(data)

def test_pca_synthetic_data(synthetic_metrics_data, tmp_path):
    """Test T023a: PCA on synthetic data."""
    # Run PCA
    pca, loadings_df, scores_df = perform_pca_on_metrics(synthetic_metrics_data)
    
    # Verify shapes
    assert loadings_df.shape[0] == 4 # 4 metrics
    assert scores_df.shape[0] == 100 # 100 subjects
    assert "pca_factor_1" in scores_df.columns
    
    # Save to verify T023a output requirements
    loadings_path = tmp_path / "pca_loadings.csv"
    scores_path = tmp_path / "factor_scores.csv"
    loadings_df.to_csv(loadings_path)
    scores_df.to_csv(scores_path)
    
    assert loadings_path.exists()
    assert scores_path.exists()

def test_full_metrics_merge(synthetic_metrics_data, tmp_path):
    """Test T023b: Merge metrics and PCA scores."""
    # First get PCA scores
    _, _, scores_df = perform_pca_on_metrics(synthetic_metrics_data)
    
    # Run merge
    full_df = generate_full_metrics(synthetic_metrics_data, scores_df)
    
    # Verify columns
    assert "modularity" in full_df.columns
    assert "pca_factor_1" in full_df.columns
    assert "subject_id" in full_df.columns
    
    # Verify count
    assert len(full_df) == len(synthetic_metrics_data)
    
    # Save
    output_path = tmp_path / "full_metrics.csv"
    save_full_metrics(full_df, str(output_path))
    assert output_path.exists()

def test_correlation_with_covariate(synthetic_metrics_data):
    """Test T024: Correlation with FD covariate."""
    # Run correlation
    corr_df = run_correlations_with_fd_covariate(synthetic_metrics_data)
    
    # Verify structure
    assert "r" in corr_df.columns
    assert "p" in corr_df.columns
    assert "covariate" in corr_df.columns
    
    # Verify we detected the injected correlation for modularity
    mod_row = corr_df[corr_df["metric"] == "modularity"]
    assert len(mod_row) == 1
    # The injected correlation was ~0.8, so r should be high
    assert abs(mod_row.iloc[0]["r"]) > 0.5

def test_fdr_correction(synthetic_metrics_data):
    """Test T025: FDR correction."""
    # Get correlations
    corr_df = run_correlations_with_fd_covariate(synthetic_metrics_data)
    
    # Apply FDR
    corrected_df = apply_fdr_correction(corr_df)
    
    # Verify columns
    assert "q" in corrected_df.columns
    assert "significant" in corrected_df.columns
    
    # Verify values are between 0 and 1
    assert (corrected_df["q"] >= 0).all()
    assert (corrected_df["q"] <= 1).all()

def test_integration_pipeline(synthetic_metrics_data, tmp_path):
    """End-to-end test of T023a -> T023b -> T024 -> T025."""
    # 1. PCA
    pca, loadings_df, scores_df = perform_pca_on_metrics(synthetic_metrics_data)
    save_pca_results(loadings_df, scores_df, str(tmp_path))
    
    # 2. Full Metrics
    full_df = generate_full_metrics(synthetic_metrics_data, scores_df)
    save_full_metrics(full_df, str(tmp_path / "full_metrics.csv"))
    
    # 3. Correlations
    corr_df = run_correlations_with_fd_covariate(full_df)
    
    # 4. FDR
    final_df = apply_fdr_correction(corr_df)
    save_correlation_results(final_df, str(tmp_path / "correlations.csv"))
    
    # Verify all files exist
    assert (tmp_path / "pca_loadings.csv").exists()
    assert (tmp_path / "factor_scores.csv").exists()
    assert (tmp_path / "full_metrics.csv").exists()
    assert (tmp_path / "correlations.csv").exists()
    
    # Verify content integrity
    assert len(final_df) == 4 # 4 metrics
