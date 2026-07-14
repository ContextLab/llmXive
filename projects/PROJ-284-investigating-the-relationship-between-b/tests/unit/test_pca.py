import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.correlations import run_pca_on_metrics, load_metrics_data

@pytest.fixture
def sample_metrics_df():
    """Create a synthetic DataFrame with required columns."""
    np.random.seed(42)
    n = 50
    data = {
        'subject_id': [f'sub-{i:03d}' for i in range(n)],
        'modularity': np.random.uniform(0.3, 0.8, n),
        'global_efficiency': np.random.uniform(0.1, 0.5, n),
        'participation_coef': np.random.uniform(0.2, 0.6, n),
        'within_module_degree': np.random.uniform(1.0, 5.0, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_processed_dir(tmp_path):
    """Create a temporary processed directory with the required CSV."""
    proc_dir = tmp_path / "data" / "processed"
    proc_dir.mkdir(parents=True)
    return proc_dir

def test_pca_loadings_and_scores_generation(sample_metrics_df, temp_processed_dir, tmp_path):
    """
    Test that run_pca_on_metrics generates the correct output files:
    - data/analysis/pca_loadings.csv
    - data/analysis/factor_scores.csv
    """
    # Mock the load_metrics_data to return our sample data
    # Since load_metrics_data reads from a fixed path, we need to simulate the file existence
    # or patch the function. For this unit test, we directly call run_pca_on_metrics
    # with the dataframe to verify the logic and file writing.
    
    # We need to temporarily override the DATA_DIR constant in the module
    # or pass the data directly. The function run_pca_on_metrics takes a DF, 
    # but the side effect is writing to ANALYSIS_DIR.
    
    # Let's patch the ANALYSIS_DIR in the correlations module
    import code.analysis.correlations as corr_mod
    original_analysis_dir = corr_mod.ANALYSIS_DIR
    
    analysis_dir = tmp_path / "data" / "analysis"
    analysis_dir.mkdir(parents=True)
    corr_mod.ANALYSIS_DIR = analysis_dir
    
    try:
        # Run PCA
        pca_info, scores_df = run_pca_on_metrics(sample_metrics_df, n_components=2)
        
        # Verify files exist
        loadings_path = analysis_dir / "pca_loadings.csv"
        scores_path = analysis_dir / "factor_scores.csv"
        
        assert loadings_path.exists(), "pca_loadings.csv was not created"
        assert scores_path.exists(), "factor_scores.csv was not created"
        
        # Verify content structure
        loadings_df = pd.read_csv(loadings_path, index_col=0)
        scores_df_read = pd.read_csv(scores_path)
        
        # Check loadings columns
        assert 'component_1' in loadings_df.columns
        assert 'component_2' in loadings_df.columns
        assert len(loadings_df) == 4 # 4 metrics
        
        # Check scores columns
        assert 'subject_id' in scores_df_read.columns
        assert 'pca_factor_1' in scores_df_read.columns
        assert 'pca_factor_2' in scores_df_read.columns
        assert len(scores_df_read) == len(sample_metrics_df)
        
        # Verify variance is positive
        assert all(v > 0 for v in pca_info['explained_variance_ratio'])
        
    finally:
        # Restore original
        corr_mod.ANALYSIS_DIR = original_analysis_dir

def test_pca_with_missing_values(sample_metrics_df, temp_processed_dir, tmp_path):
    """Test that PCA handles missing values gracefully (drops them)."""
    import code.analysis.correlations as corr_mod
    
    # Introduce NaN
    df_with_nan = sample_metrics_df.copy()
    df_with_nan.loc[0, 'modularity'] = np.nan
    
    analysis_dir = tmp_path / "data" / "analysis"
    analysis_dir.mkdir(parents=True)
    original_dir = corr_mod.ANALYSIS_DIR
    corr_mod.ANALYSIS_DIR = analysis_dir
    
    try:
        # Should not raise, should drop the row
        pca_info, scores_df = run_pca_on_metrics(df_with_nan, n_components=2)
        
        assert len(scores_df) == len(sample_metrics_df) - 1
        
        loadings_path = analysis_dir / "pca_loadings.csv"
        assert loadings_path.exists()
        
    finally:
        corr_mod.ANALYSIS_DIR = original_dir
