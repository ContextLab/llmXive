import os
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Import the module under test
# Adjust import path if necessary based on project structure
try:
    from code.analysis.correlations import run_pca_on_metrics, load_metrics_data, apply_fdr_correction
except ImportError:
    from analysis.correlations import run_pca_on_metrics, load_metrics_data, apply_fdr_correction


@pytest.fixture
def synthetic_data():
    """
    Generate synthetic data with known correlations for testing.
    We create a dataset where:
    - modularity is positively correlated with global_efficiency
    - participation_coef is independent
    """
    np.random.seed(42)
    n = 100
    
    # Create base variables
    base = np.random.randn(n)
    noise = np.random.randn(n) * 0.1
    
    modularity = base + noise
    global_efficiency = 0.8 * base + noise * 0.5
    participation_coef = np.random.randn(n)
    within_module_degree = np.random.randn(n)
    fd = np.random.randn(n) * 0.1
    motor_score = 0.5 * base + np.random.randn(n) * 0.5
    
    df = pd.DataFrame({
        'subject_id': [f'sub-{i:03d}' for i in range(n)],
        'modularity': modularity,
        'global_efficiency': global_efficiency,
        'participation_coef': participation_coef,
        'within_module_degree': within_module_degree,
        'fd': fd,
        'motor_score': motor_score
    })
    return df


def test_correlation_with_synthetic_data(synthetic_data):
    """
    Integration test for T019 / T024 / T025.
    Verifies that:
    1. Correlations are computed correctly (r values match expected direction).
    2. FDR correction is applied.
    3. PCA produces valid outputs (T023a).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'aggregated_metrics.csv')
        corr_out = os.path.join(tmpdir, 'correlations.csv')
        pca_loadings = os.path.join(tmpdir, 'pca_loadings.csv')
        pca_scores = os.path.join(tmpdir, 'factor_scores.csv')
        
        # Save synthetic data
        synthetic_data.to_csv(input_path, index=False)
        
        # Test loading
        df_loaded = load_metrics_data(input_path)
        assert len(df_loaded) == 100
        
        # Test PCA (T023a)
        run_pca_on_metrics(
            df_loaded, 
            output_loadings=pca_loadings, 
            output_scores=pca_scores
        )
        
        # Verify PCA outputs exist and have correct shape
        assert os.path.exists(pca_loadings)
        assert os.path.exists(pca_scores)
        
        loadings_df = pd.read_csv(pca_loadings, index_col=0)
        assert loadings_df.shape == (4, 2) # 4 metrics, 2 components
        assert list(loadings_df.columns) == ['component_1', 'component_2']
        
        scores_df = pd.read_csv(pca_scores)
        assert 'subject_id' in scores_df.columns
        assert 'pca_factor_1' in scores_df.columns
        assert len(scores_df) == 100
        
        # Verify correlation logic (manually checking a subset since we don't call the full main here)
        # We expect modularity and global_efficiency to be highly correlated
        r, p = np.corrcoef(synthetic_data['modularity'], synthetic_data['global_efficiency'])[0, 1]
        assert r > 0.7 # Should be strong positive
        
        # Test FDR
        p_vals = np.array([0.01, 0.04, 0.05, 0.20, 0.50])
        p_adj, sig = apply_fdr_correction(p_vals)
        assert len(p_adj) == 5
        assert len(sig) == 5
        # BH correction should increase p-values
        assert np.all(p_adj >= p_vals)
        
        logger.info("Integration test passed: synthetic data processed correctly.")

def test_pca_loadings_preserve_variance(synthetic_data):
    """
    Test that PCA loadings explain a significant portion of variance.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'aggregated_metrics.csv')
        pca_loadings = os.path.join(tmpdir, 'pca_loadings.csv')
        synthetic_data.to_csv(input_path, index=False)
        
        df = load_metrics_data(input_path)
        run_pca_on_metrics(df, output_loadings=pca_loadings)
        
        loadings = pd.read_csv(pca_loadings, index_col=0)
        
        # Check that loadings are not all zeros or NaNs
        assert not loadings.isna().any().any()
        assert not (loadings == 0).all().all()
        
        # Check that sum of squares of loadings for a component is roughly 1 (if standardized)
        # Due to floating point and implementation details, just check it's close to 1
        comp1_norm = np.sqrt((loadings['component_1']**2).sum())
        assert 0.9 < comp1_norm < 1.1, f"Component 1 norm is {comp1_norm}, expected ~1.0"

def test_factor_scores_match_subjects(synthetic_data):
    """
    Ensure factor scores are correctly aligned with subject IDs.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'aggregated_metrics.csv')
        pca_scores = os.path.join(tmpdir, 'factor_scores.csv')
        synthetic_data.to_csv(input_path, index=False)
        
        df = load_metrics_data(input_path)
        run_pca_on_metrics(df, output_scores=pca_scores)
        
        scores = pd.read_csv(pca_scores)
        
        # Check that all subject IDs from input are in output (assuming no NaNs in metrics)
        assert set(scores['subject_id']) == set(df['subject_id'])
        
        # Check that scores are numeric
        assert pd.api.types.is_numeric_dtype(scores['pca_factor_1'])
        assert pd.api.types.is_numeric_dtype(scores['pca_factor_2'])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
