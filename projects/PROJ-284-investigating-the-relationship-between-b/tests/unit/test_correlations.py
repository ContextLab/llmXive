import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from code.analysis.correlations import load_metrics_data, run_pca_on_metrics, generate_full_metrics

class TestPCATask:
    """Tests for T023a: PCA on network metrics."""

    @pytest.fixture
    def sample_metrics_df(self):
        """Creates a synthetic DataFrame with required metrics."""
        np.random.seed(42)
        n = 50
        data = {
            'subject_id': [f"sub-{i:03d}" for i in range(n)],
            'modularity': np.random.uniform(0.3, 0.8, n),
            'global_efficiency': np.random.uniform(0.1, 0.4, n),
            'participation_coef': np.random.uniform(0.2, 0.6, n),
            'within_module_degree': np.random.uniform(1.0, 5.0, n)
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_data_dir(self, sample_metrics_df):
        """Sets up a temporary directory structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create necessary directories
            processed_dir = Path(tmpdir) / "data" / "processed"
            analysis_dir = Path(tmpdir) / "data" / "analysis"
            processed_dir.mkdir(parents=True)
            analysis_dir.mkdir(parents=True)
            
            # Save sample data
            csv_path = processed_dir / "aggregated_metrics.csv"
            sample_metrics_df.to_csv(csv_path, index=False)
            
            # Patch the global PROJECT_ROOT in correlations.py for this test
            # We do this by temporarily modifying the module's attribute
            import code.analysis.correlations as corr_module
            original_root = corr_module.PROJECT_ROOT
            corr_module.PROJECT_ROOT = Path(tmpdir)
            corr_module.DATA_PROCESSED_DIR = processed_dir
            corr_module.DATA_ANALYSIS_DIR = analysis_dir
            
            yield analysis_dir, csv_path
            
            # Restore original
            corr_module.PROJECT_ROOT = original_root
            corr_module.DATA_PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data"
            corr_module.DATA_ANALYSIS_DIR = Path(__file__).resolve().parents[2] / "data" / "analysis"

    def test_pca_loadings_generated(self, temp_data_dir):
        """Verifies that pca_loadings.csv is created with correct columns."""
        analysis_dir, _ = temp_data_dir
        
        # Run PCA
        _, _ = run_pca_on_metrics(load_metrics_data())
        
        # Check file existence
        loadings_path = analysis_dir / "pca_loadings.csv"
        assert loadings_path.exists(), "pca_loadings.csv was not created."
        
        # Check content
        df = pd.read_csv(loadings_path, index_col=0) # Index is metric name
        assert 'component_1' in df.columns
        assert 'component_2' in df.columns
        assert len(df) == 4 # 4 metrics
        
    def test_factor_scores_generated(self, temp_data_dir):
        """Verifies that factor_scores.csv is created with correct columns."""
        analysis_dir, _ = temp_data_dir
        
        # Run PCA
        _, _ = run_pca_on_metrics(load_metrics_data())
        
        # Check file existence
        scores_path = analysis_dir / "factor_scores.csv"
        assert scores_path.exists(), "factor_scores.csv was not created."
        
        # Check content
        df = pd.read_csv(scores_path)
        assert 'subject_id' in df.columns
        assert 'pca_factor_1' in df.columns
        assert len(df) == 50 # Matches input
        
    def test_full_metrics_generated(self, temp_data_dir):
        """Verifies that full_metrics.csv merges raw and PCA data."""
        analysis_dir, _ = temp_data_dir
        
        # Run full pipeline
        df = load_metrics_data()
        _, scores = run_pca_on_metrics(df)
        full_df = generate_full_metrics(df, scores)
        
        # Check file existence
        full_path = analysis_dir / "full_metrics.csv"
        assert full_path.exists(), "full_metrics.csv was not created."
        
        # Check content
        loaded_full = pd.read_csv(full_path)
        assert 'subject_id' in loaded_full.columns
        assert 'modularity' in loaded_full.columns
        assert 'pca_factor_1' in loaded_full.columns
        assert len(loaded_full) == 50