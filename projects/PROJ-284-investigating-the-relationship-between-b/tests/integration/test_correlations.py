"""
Integration test for US2 Correlation Analysis.
Tests T023b: File Output & Metric Preservation.
"""
import os
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

from code.analysis.correlations import (
    perform_pca_on_metrics,
    save_pca_results,
    merge_metrics_with_pca_scores,
    generate_full_metrics_output,
    main
)


@pytest.fixture
def sample_metrics_df():
    """Generate a synthetic DataFrame matching the expected schema from T021/T022."""
    n = 100
    data = {
        'subject_id': [f'sub-{i:03d}' for i in range(n)],
        'modularity': np.random.uniform(0.3, 0.7, n),
        'global_efficiency': np.random.uniform(0.1, 0.5, n),
        'participation_coef': np.random.uniform(0.0, 0.3, n),
        'within_module_degree': np.random.uniform(0.5, 2.0, n)
    }
    return pd.DataFrame(data)


def test_correlation_with_synthetic_data(sample_metrics_df, tmp_path):
    """
    Integration test: Verify that the analysis pipeline produces correct statistical outputs
    and writes the required CSV files (T023b) when run on synthetic data with known properties.
    
    Verifies:
    1. PCA runs without error.
    2. Loadings and scores are saved to correct paths.
    3. Full metrics file contains all raw columns + PCA factors.
    """
    # Mock the data directory structure
    data_analysis_dir = tmp_path / "data" / "analysis"
    data_analysis_dir.mkdir(parents=True)
    
    # Temporarily override the module's path constants for testing
    import code.analysis.correlations as corr_module
    original_dir = corr_module.DATA_ANALYSIS_DIR
    original_processed = corr_module.DATA_PROCESSED_DIR
    
    corr_module.DATA_ANALYSIS_DIR = data_analysis_dir
    corr_module.DATA_PROCESSED_DIR = tmp_path / "data" / "processed"
    (tmp_path / "data" / "processed").mkdir(parents=True)

    try:
        # 1. Perform PCA
        pca, loadings_df, scores_df = perform_pca_on_metrics(sample_metrics_df)
        
        # Verify PCA results shape
        assert loadings_df.shape == (4, 2), "Loadings should have 4 rows (metrics) and 2 cols (components)"
        assert scores_df.shape == (100, 3), "Scores should have 100 rows and 3 cols (id + 2 factors)"
        
        # 2. Save Results
        save_pca_results(loadings_df, scores_df)
        
        # Verify files exist
        assert (data_analysis_dir / "pca_loadings.csv").exists()
        assert (data_analysis_dir / "factor_scores.csv").exists()
        
        # 3. Merge
        merged_df = merge_metrics_with_pca_scores(sample_metrics_df, scores_df)
        
        # Verify merge integrity
        assert len(merged_df) == 100
        assert 'pca_factor_1' in merged_df.columns
        assert 'pca_factor_2' in merged_df.columns
        assert 'modularity' in merged_df.columns
        
        # 4. Generate Full Output (T023b specific)
        generate_full_metrics_output(merged_df)
        
        # Verify final output file
        full_metrics_path = data_analysis_dir / "full_metrics.csv"
        assert full_metrics_path.exists(), "full_metrics.csv must be written"
        
        final_df = pd.read_csv(full_metrics_path)
        assert len(final_df) == 100
        # Check for presence of all required columns
        required_cols = ['subject_id', 'modularity', 'global_efficiency', 'participation_coef', 
                         'within_module_degree', 'pca_factor_1', 'pca_factor_2']
        for col in required_cols:
            assert col in final_df.columns, f"Missing column {col} in full_metrics.csv"
            
        # 5. Verify statistical consistency (optional but good for integration)
        # Check that PCA factor_1 has some variance (not constant)
        assert final_df['pca_factor_1'].var() > 1e-6, "PCA factor should have variance"
        
    finally:
        # Restore original paths
        corr_module.DATA_ANALYSIS_DIR = original_dir
        corr_module.DATA_PROCESSED_DIR = original_processed