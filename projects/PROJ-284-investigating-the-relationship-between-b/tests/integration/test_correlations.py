"""
Integration tests for the correlation analysis module.
Tests T023a (PCA) and T024/T025 (Correlations/FDR) using synthetic data.
"""
import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from code.analysis.correlations import (
    load_metrics_data,
    run_pca_on_metrics,
    save_pca_results,
    run_correlations_with_fd_covariate,
    apply_fdr_correction,
    generate_full_metrics
)

# Fixtures
@pytest.fixture
def sample_metrics_df(tmp_path):
    """Create a synthetic dataset with known correlations for testing."""
    np.random.seed(42)
    n = 100
    data = {
        "subject_id": [f"sub_{i:03d}" for i in range(n)],
        "modularity": np.random.rand(n),
        "global_efficiency": np.random.rand(n),
        "participation_coef": np.random.rand(n),
        "within_module_degree": np.random.rand(n),
        "fd": np.random.rand(n) * 0.5,
        "motor_score": np.random.rand(n)
    }
    # Introduce a known correlation for testing
    data["motor_score"] = data["modularity"] * 0.8 + np.random.normal(0, 0.1, n)

    df = pd.DataFrame(data)
    output_path = tmp_path / "aggregated_metrics.csv"
    df.to_csv(output_path, index=False)
    return df, output_path

def test_pca_loadings_and_scores(sample_metrics_df, tmp_path):
    """
    Test T023a: Verify PCA produces valid loadings and scores with correct shapes.
    """
    df, input_path = sample_metrics_df

    # Temporarily override the input path for the function
    import code.analysis.correlations as corr_module
    original_path = corr_module.METRICS_INPUT_PATH
    corr_module.METRICS_INPUT_PATH = input_path

    try:
        # Run load
        loaded_df = load_metrics_data()
        assert loaded_df.shape == df.shape
        assert "subject_id" in loaded_df.columns

        # Run PCA
        pca, loadings, scores = run_pca_on_metrics(loaded_df)

        # Verify shapes
        assert loadings.shape == (2, 4), f"Loadings shape mismatch: {loadings.shape}"
        assert scores.shape == (100, 2), f"Scores shape mismatch: {scores.shape}"

        # Verify save
        save_pca_results(pca, loadings, scores, loaded_df)

        # Verify output files exist and have correct columns
        assert Path("data/analysis/pca_loadings.csv").exists()
        assert Path("data/analysis/factor_scores.csv").exists()

        loadings_csv = pd.read_csv("data/analysis/pca_loadings.csv")
        assert "component_1" in loadings_csv.columns
        assert "component_2" in loadings_csv.columns

        scores_csv = pd.read_csv("data/analysis/factor_scores.csv")
        assert "subject_id" in scores_csv.columns
        assert "pca_factor_1" in scores_csv.columns
        assert scores_csv.columns.tolist() == ["subject_id", "pca_factor_1"]

    finally:
        # Restore original path
        corr_module.METRICS_INPUT_PATH = original_path

def test_correlation_with_synthetic_data(sample_metrics_df, tmp_path):
    """
    Test T024/T025: Verify correlation analysis detects the known correlation
    and FDR correction works correctly.
    """
    df, input_path = sample_metrics_df

    import code.analysis.correlations as corr_module
    original_path = corr_module.METRICS_INPUT_PATH
    corr_module.METRICS_INPUT_PATH = input_path

    try:
        loaded_df = load_metrics_data()

        # Run correlation
        results = run_correlations_with_fd_covariate(loaded_df)
        assert "r" in results.columns
        assert "p" in results.columns

        # Check that modularity has a significant correlation (since we injected it)
        mod_row = results[results["metric"] == "modularity"]
        assert len(mod_row) == 1
        # With our synthetic data, r should be high and p low
        assert mod_row["r"].values[0] > 0.5, f"Expected high r for modularity, got {mod_row['r'].values[0]}"
        assert mod_row["p"].values[0] < 0.05, f"Expected low p for modularity, got {mod_row['p'].values[0]}"

        # Apply FDR
        fdr_results = apply_fdr_correction(results)
        assert "q" in fdr_results.columns
        assert "significant" in fdr_results.columns

        # Check that modularity is still significant after FDR
        mod_fdr = fdr_results[fdr_results["metric"] == "modularity"]
        assert mod_fdr["significant"].values[0] is True

    finally:
        corr_module.METRICS_INPUT_PATH = original_path