"""
Integration tests for the correlation analysis module.
Tests T023a (PCA) and T024/T025 (Correlations/FDR) using synthetic data.
"""
import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from code.analysis.correlations import (
    load_metrics_data,
    run_pca_on_metrics,
    run_correlations_with_fd_covariate,
    apply_fdr_correction,
    generate_full_metrics,
    save_pca_results
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
    # motor_score is strongly correlated with modularity
    data["motor_score"] = data["modularity"] * 0.8 + np.random.normal(0, 0.1, n)

    df = pd.DataFrame(data)
    # Write to a temporary file to simulate the input file
    output_path = tmp_path / "aggregated_metrics.csv"
    df.to_csv(output_path, index=False)
    return df, output_path

def test_pca_loadings_and_scores(sample_metrics_df, tmp_path):
    """
    Integration test for T024 and T025:
    Runs correlation analysis with synthetic data and verifies FDR correction.
    """

    # Temporarily override the input path for the function
    import code.analysis.correlations as corr_module
    original_path = getattr(corr_module, 'METRICS_INPUT_PATH', None)
    corr_module.METRICS_INPUT_PATH = input_path

    def test_correlation_pipeline_runs(self):
        """Verify the full correlation pipeline runs without error."""
        # Load
        df = load_metrics_data(self.test_file)
        assert len(df) == 50
        
        # Run Correlations
        corr_df = run_correlations_with_fd_covariate(df)
        assert 'metric_name' in corr_df.columns
        assert 'r' in corr_df.columns
        assert 'p' in corr_df.columns
        assert len(corr_df) > 0
        
        # Run FDR
        corr_df_fdr = apply_fdr_correction(corr_df)
        assert 'q' in corr_df_fdr.columns
        assert 'significant' in corr_df_fdr.columns
        
        # Verify FDR logic: q values should be >= p values (monotonicity adjusted)
        # In BH, q_i = p_i * m / i (roughly), so q >= p usually.
        # Check that q is not NaN
        assert not corr_df_fdr['q'].isna().any()

    def test_fdr_on_known_data(self):
        """
        Test FDR correction on data where we inject a strong correlation.
        We expect at least one metric to be significant after FDR if the signal is strong enough.
        """
        # Inject strong correlation for 'modularity'
        self.test_df['motor_score_injected'] = self.test_df['modularity'] * 50 + np.random.normal(0, 1, len(self.test_df))
        
        # Modify the run function to use this new column? 
        # Or just test the apply_fdr_correction function directly with known p-values.
        
        # Create a mock result dataframe with known p-values
        mock_results = pd.DataFrame({
            'metric_name': ['m1', 'm2', 'm3', 'm4'],
            'r': [0.1, 0.1, 0.1, 0.1],
            'p': [0.5, 0.01, 0.001, 0.05] # Sorted roughly
        })
        
        corrected = apply_fdr_correction(mock_results)
        
        # Verify q values are calculated
        assert not corrected['q'].isna().any()
        assert all(corrected['q'] >= 0)
        assert all(corrected['q'] <= 1)
        
        # The smallest p (0.001) should likely be significant if alpha=0.05
        # m=4.
        # p=0.001 -> rank 1? No, sorted: 0.001, 0.01, 0.05, 0.5
        # i=1: 0.001 <= (1/4)*0.05 = 0.0125 -> True
        # i=2: 0.01 <= (2/4)*0.05 = 0.025 -> True
        # i=3: 0.05 <= (3/4)*0.05 = 0.0375 -> False
        # i=4: 0.5 <= 0.05 -> False
        # So first two should be significant.
        assert corrected.loc[corrected['p'] == 0.001, 'significant'].values[0] == True
        assert corrected.loc[corrected['p'] == 0.01, 'significant'].values[0] == True

        # Verify shapes
        # We expect 2 components and 4 metrics (modularity, global_eff, part_coef, wmd)
        assert loadings.shape == (2, 4), f"Loadings shape mismatch: {loadings.shape}"
        assert scores.shape == (100, 2), f"Scores shape mismatch: {scores.shape}"

        # Run save (this writes to the project's data/analysis directory)
        # We need to ensure the directory exists
        os.makedirs("data/analysis", exist_ok=True)
        save_pca_results(pca, loadings, scores, loaded_df)

        # Verify output files exist and have correct columns
        assert Path("data/analysis/pca_loadings.csv").exists(), "pca_loadings.csv not found"
        assert Path("data/analysis/factor_scores.csv").exists(), "factor_scores.csv not found"

        loadings_csv = pd.read_csv("data/analysis/pca_loadings.csv")
        assert "component_1" in loadings_csv.columns
        assert "component_2" in loadings_csv.columns

        scores_csv = pd.read_csv("data/analysis/factor_scores.csv")
        assert "subject_id" in scores_csv.columns
        assert "pca_factor_1" in scores_csv.columns
        # The test spec expects exactly these two columns
        assert scores_csv.columns.tolist() == ["subject_id", "pca_factor_1"]

    finally:
        # Restore original path
        if original_path is not None:
            corr_module.METRICS_INPUT_PATH = original_path
        else:
            if hasattr(corr_module, 'METRICS_INPUT_PATH'):
                delattr(corr_module, 'METRICS_INPUT_PATH')

def test_correlation_with_synthetic_data(sample_metrics_df, tmp_path):
    """
    Test T024/T025: Verify correlation analysis detects the known correlation
    and FDR correction works correctly.
    """
    df, input_path = sample_metrics_df

    import code.analysis.correlations as corr_module
    original_path = getattr(corr_module, 'METRICS_INPUT_PATH', None)
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
        # The injected correlation is 0.8, so we expect r > 0.5
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
        if original_path is not None:
            corr_module.METRICS_INPUT_PATH = original_path
        else:
            if hasattr(corr_module, 'METRICS_INPUT_PATH'):
                delattr(corr_module, 'METRICS_INPUT_PATH')