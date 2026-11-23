import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.graph_metrics.calculator import check_collinearity, apply_pca, run_collinearity_check_and_reduction

class TestCollinearity:
    
    def test_check_collinearity_no_high_corr(self, tmp_path):
        """Test that no features are dropped when correlations are low."""
        # Create a dataframe with low correlations
        np.random.seed(42)
        data = {
            'subject_id': [f'sub-{i}' for i in range(10)],
            'feature1': np.random.randn(10),
            'feature2': np.random.randn(10),
            'feature3': np.random.randn(10)
        }
        df = pd.DataFrame(data)
        
        reduced_df, dropped, pca_applied = check_collinearity(df, threshold=0.8)
        
        assert len(dropped) == 0
        assert pca_applied is False
        assert list(reduced_df.columns) == list(df.columns)
    
    def test_check_collinearity_high_corr(self, tmp_path):
        """Test that highly correlated features are identified and dropped."""
        # Create a dataframe with high correlation
        np.random.seed(42)
        base = np.random.randn(10)
        data = {
            'subject_id': [f'sub-{i}' for i in range(10)],
            'feature1': base,
            'feature2': base * 0.95 + np.random.randn(10) * 0.1,  # Highly correlated
            'feature3': np.random.randn(10)
        }
        df = pd.DataFrame(data)
        
        reduced_df, dropped, pca_applied = check_collinearity(df, threshold=0.8)
        
        assert len(dropped) > 0
        assert 'feature2' in dropped or 'feature1' in dropped
        assert len(reduced_df.columns) < len(df.columns)
    
    def test_apply_pca(self):
        """Test PCA application reduces dimensions."""
        np.random.seed(42)
        data = {
            'subject_id': [f'sub-{i}' for i in range(20)],
            'f1': np.random.randn(20),
            'f2': np.random.randn(20),
            'f3': np.random.randn(20),
            'f4': np.random.randn(20),
            'f5': np.random.randn(20)
        }
        df = pd.DataFrame(data)
        
        pca_df, info = apply_pca(df, variance_threshold=0.95)
        
        assert 'subject_id' in pca_df.columns
        assert 'PC1' in pca_df.columns
        assert info['n_components'] <= 5
        assert sum(info['explained_variance_ratio']) >= 0.95
    
    def test_run_collinearity_check_and_reduction_integration(self, tmp_path):
        """Test full collinearity pipeline."""
        # Setup paths
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        processed_dir = data_dir / "processed"
        processed_dir.mkdir()
        metadata_dir = data_dir / "metadata"
        metadata_dir.mkdir()
        
        # Create test data with collinearity
        np.random.seed(42)
        base = np.random.randn(15)
        data = {
            'subject_id': [f'sub-{i}' for i in range(15)],
            'efficiency': base,
            'efficiency_copy': base * 0.9 + np.random.randn(15) * 0.1,
            'modularity': np.random.randn(15),
            'centrality': np.random.randn(15)
        }
        df = pd.DataFrame(data)
        
        # Run pipeline
        result = run_collinearity_check_and_reduction(
            df,
            save_pca_path=str(processed_dir / "features_pca.csv"),
            save_log_path=str(metadata_dir / "collinearity_log.txt")
        )
        
        # Verify outputs
        assert result is not None
        assert result.shape[0] == 15
        
        # Check log file was created
        log_path = metadata_dir / "collinearity_log.txt"
        assert log_path.exists()
        
        with open(log_path, 'r') as f:
            content = f.read()
            assert "Collinearity" in content
            assert "threshold" in content.lower()
    
    def test_collinearity_log_content(self, tmp_path):
        """Verify collinearity log contains required information."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        metadata_dir = data_dir / "metadata"
        metadata_dir.mkdir()
        
        np.random.seed(42)
        base = np.random.randn(10)
        data = {
            'subject_id': [f'sub-{i}' for i in range(10)],
            'f1': base,
            'f2': base * 0.95
        }
        df = pd.DataFrame(data)
        
        run_collinearity_check_and_reduction(
            df,
            save_log_path=str(metadata_dir / "collinearity_log.txt")
        )
        
        log_path = metadata_dir / "collinearity_log.txt"
        with open(log_path, 'r') as f:
            content = f.read()
            
        # Check required sections
        assert "Threshold" in content
        assert "Features identified" in content
        assert "Action taken" in content