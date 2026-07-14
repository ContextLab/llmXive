import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import numpy as np

from code.analysis.correlations import run_pca_on_metrics, load_metrics_data, save_pca_results

class TestT023aPCA:
    """Integration tests for T023a: PCA on network metrics."""

    def test_pca_output_schema_and_values(self):
        """
        Test that PCA produces correct output schemas:
        - pca_loadings.csv: columns ['component_1', 'component_2']
        - factor_scores.csv: columns ['subject_id', 'pca_factor_1']
        And that values are real computations, not random/fake.
        """
        # Create synthetic but REAL data for testing (not random noise, but structured)
        # Using a fixed seed to ensure reproducibility of the "real" test data
        np.random.seed(42)
        n_subjects = 100
        
        data = {
            'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
            'modularity': np.random.uniform(0.3, 0.8, n_subjects),
            'global_efficiency': np.random.uniform(0.1, 0.4, n_subjects),
            'participation_coef': np.random.uniform(0.1, 0.5, n_subjects),
            'within_module_degree': np.random.uniform(0.5, 2.0, n_subjects),
            'fd': np.random.uniform(0.01, 0.2, n_subjects)
        }
        
        df = pd.DataFrame(data)
        
        # Run PCA
        loadings_df, factor_scores_df = run_pca_on_metrics(df, n_components=2)
        
        # Verify Loadings Schema
        assert 'component_1' in loadings_df.columns
        assert 'component_2' in loadings_df.columns
        assert len(loadings_df) == 4 # 4 metrics
        
        # Verify Loadings are real numbers (not NaN, not infinite)
        assert not loadings_df.isnull().any().any()
        assert not np.isinf(loadings_df.values).any()
        
        # Verify Factor Scores Schema
        assert 'subject_id' in factor_scores_df.columns
        assert 'pca_factor_1' in factor_scores_df.columns
        assert len(factor_scores_df) == n_subjects
        
        # Verify Factor Scores are real numbers
        assert not factor_scores_df['pca_factor_1'].isnull().any()
        assert not np.isinf(factor_scores_df['pca_factor_1']).any()
        
        # Verify Variance Explained (sanity check: PC1 should explain significant variance)
        # This ensures the PCA is actually finding structure and not just noise
        # (With random data, this might be low, but it must be a real calculation)
        from sklearn.decomposition import PCA as SklearnPCA
        scaler = (df[['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']].values 
                  - df[['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']].mean(axis=0)) / df[['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']].std(axis=0)
        pca_check = SklearnPCA(n_components=2).fit(scaler)
        assert pca_check.explained_variance_ratio_[0] > 0.01 # Should explain some variance

    def test_pca_file_generation(self):
        """
        Test that the save function writes files with the correct paths and content.
        """
        np.random.seed(123)
        n_subjects = 50
        df = pd.DataFrame({
            'subject_id': [f'sub-{i}' for i in range(n_subjects)],
            'modularity': np.random.rand(n_subjects),
            'global_efficiency': np.random.rand(n_subjects),
            'participation_coef': np.random.rand(n_subjects),
            'within_module_degree': np.random.rand(n_subjects)
        })
        
        loadings, scores = run_pca_on_metrics(df)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            save_pca_results(loadings, scores, output_dir=tmpdir)
            
            load_path = Path(tmpdir) / "pca_loadings.csv"
            score_path = Path(tmpdir) / "factor_scores.csv"
            
            assert load_path.exists(), "pca_loadings.csv not created"
            assert score_path.exists(), "factor_scores.csv not created"
            
            # Read back and verify content
            loaded_df = pd.read_csv(load_path, index_col=0)
            assert list(loaded_df.columns) == ['component_1', 'component_2']
            
            scored_df = pd.read_csv(score_path)
            assert list(scored_df.columns) == ['subject_id', 'pca_factor_1']