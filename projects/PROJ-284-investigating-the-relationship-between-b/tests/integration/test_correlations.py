"""
Integration test for T023a, T023b, T024, T025.
Verifies synthetic data correlation analysis pipeline.

NOTE: This test uses synthetic data to verify the statistical pipeline
(PCA, Correlation, FDR) without requiring real HCP downloads.
The data generation is deterministic (seed=42) to ensure reproducibility.
"""
import numpy as np
import pandas as pd
from code.analysis.correlations import run_correlations_with_fd_covariate, apply_fdr_correction


@pytest.fixture
def synthetic_metrics_data():
    """Generates a synthetic dataset with known correlations.
    
    Creates 100 subjects with 4 network metrics and a motor score.
    Injects a known strong correlation (r ~ 0.8) between modularity and motor_score
    to verify the pipeline detects it.
    """
    np.random.seed(42)
    n = 100
    
    # Generate base metrics (random uniform)
    modularity = np.random.rand(n)
    global_efficiency = np.random.rand(n)
    participation_coef = np.random.rand(n)
    within_module_degree = np.random.rand(n)
    
    # Generate motion data (low motion as per typical clean data)
    mean_fd = np.random.rand(n) * 0.5
    
    # Inject known correlation: motor_score = 0.8 * modularity + noise
    # This ensures we have a ground truth to verify against
    noise = np.random.normal(0, 0.1, n)
    motor_score = (modularity * 0.8) + noise
    
    data = {
        "subject_id": [f"sub_{i:03d}" for i in range(n)],
        "modularity": modularity,
        "global_efficiency": global_efficiency,
        "participation_coef": participation_coef,
        "within_module_degree": within_module_degree,
        "MeanFD": mean_fd,
        "motor_score": motor_score
    }
    
    # Create synthetic data with known correlation
    # y = 2*x + noise
    x = np.random.randn(n_subjects)
    noise = np.random.randn(n_subjects) * 0.5
    y = 2 * x + noise
    
    # Verify shapes
    # We expect 4 metrics as input
    assert loadings_df.shape[0] == 4, f"Expected 4 rows (metrics), got {loadings_df.shape[0]}"
    # We expect 100 subjects
    assert scores_df.shape[0] == 100, f"Expected 100 subjects, got {scores_df.shape[0]}"
    # Check for expected column
    assert "pca_factor_1" in scores_df.columns, "Missing pca_factor_1 column"
    
    # Run correlation (metric vs score, controlling for FD)
    # Note: run_correlations_with_fd_covariate expects specific column names
    # We adapt the synthetic data to match expected schema
    df_renamed = df.rename(columns={
        'metric_val': 'participation_coef_mean',
        'score': 'motor_score',
        'fd': 'fd'
    })
    
    assert loadings_path.exists(), "pca_loadings.csv not written"
    assert scores_path.exists(), "factor_scores.csv not written"

def test_full_metrics_merge(synthetic_metrics_data, tmp_path):
    """Test T023b: Merge metrics and PCA scores."""
    # First get PCA scores
    _, _, scores_df = perform_pca_on_metrics(synthetic_metrics_data)
    
    # Run correlations
    results = run_correlations_with_fd_covariate(
        df_renamed,
        metric_cols=['participation_coef_mean', 'modularity', 'global_efficiency', 'within_module_degree_mean'],
        outcome_col='motor_score',
        covariate_col='fd'
    )
    
    # Verify columns exist
    assert "modularity" in full_df.columns, "Missing modularity column"
    assert "pca_factor_1" in full_df.columns, "Missing pca_factor_1 column"
    assert "subject_id" in full_df.columns, "Missing subject_id column"
    
    # Verify row count matches input
    assert len(full_df) == len(synthetic_metrics_data), "Row count mismatch after merge"
    
    # Save
    output_path = tmp_path / "full_metrics.csv"
    save_full_metrics(full_df, str(output_path))
    assert output_path.exists(), "full_metrics.csv not written"

def test_correlation_with_covariate(synthetic_metrics_data):
    """Test T024: Correlation with FD covariate."""
    # Run correlation
    corr_df = run_correlations_with_fd_covariate(synthetic_metrics_data)
    
    # Verify structure
    assert "r" in corr_df.columns, "Missing 'r' column"
    assert "p" in corr_df.columns, "Missing 'p' column"
    assert "covariate" in corr_df.columns, "Missing 'covariate' column"
    
    # Verify we detected the injected correlation for modularity
    # The injected correlation was ~0.8, so r should be high (significantly > 0.5)
    mod_row = corr_df[corr_df["metric"] == "modularity"]
    assert len(mod_row) == 1, f"Expected exactly 1 row for modularity, got {len(mod_row)}"
    
    r_val = mod_row.iloc[0]["r"]
    assert abs(r_val) > 0.5, f"Detected correlation r={r_val} is too low for injected signal (~0.8)"

def test_fdr_correction(synthetic_metrics_data):
    """Test T025: FDR correction."""
    # Get correlations
    corr_df = run_correlations_with_fd_covariate(synthetic_metrics_data)
    
    # Apply FDR
    corrected_df = apply_fdr_correction(corr_df)
    
    # Verify columns
    assert "q" in corrected_df.columns, "Missing 'q' column"
    assert "significant" in corrected_df.columns, "Missing 'significant' column"
    
    # Verify values are between 0 and 1
    assert (corrected_df["q"] >= 0).all(), "q-values < 0 detected"
    assert (corrected_df["q"] <= 1).all(), "q-values > 1 detected"

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
    assert (tmp_path / "pca_loadings.csv").exists(), "pca_loadings.csv missing"
    assert (tmp_path / "factor_scores.csv").exists(), "factor_scores.csv missing"
    assert (tmp_path / "full_metrics.csv").exists(), "full_metrics.csv missing"
    assert (tmp_path / "correlations.csv").exists(), "correlations.csv missing"
    
    # Verify content integrity
    # We have 4 metrics: modularity, global_efficiency, participation_coef, within_module_degree
    assert len(final_df) == 4, f"Expected 4 correlation rows, got {len(final_df)}"