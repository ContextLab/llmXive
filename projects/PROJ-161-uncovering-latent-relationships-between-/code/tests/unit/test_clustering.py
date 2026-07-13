import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

from src.analysis.clustering import (
    load_umap_embedding,
    load_resistance_labels,
    run_dbscan,
    perform_fisher_exact_test,
    run_label_permutation_test,
    save_clustering_results,
    run_clustering_pipeline
)
from src.config import get_project_root, get_data_processed_path

@pytest.fixture
def sample_embedding():
    """Create a sample UMAP embedding DataFrame."""
    data = {
        'index': range(100),
        'umap_1': np.random.randn(100),
        'umap_2': np.random.randn(100),
        'resistance_label': ['high'] * 50 + ['low'] * 50
    }
    return pd.DataFrame(data).set_index('index')

@pytest.fixture
def sample_resistance():
    """Create a sample resistance labels Series."""
    return pd.Series(['high'] * 50 + ['low'] * 50, name='resistance_label')

@pytest.fixture
def temp_processed_dir():
    """Create a temporary directory for processed data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # We need to mock the get_data_processed_path function
        # But for now, let's just return the path
        yield Path(tmpdir)

class TestDBSCANClustering:
    def test_run_dbscan_basic(self, sample_embedding, temp_processed_dir):
        """Test basic DBSCAN clustering functionality."""
        # Mock the save function or just test the logic
        df, metadata = run_dbscan(sample_embedding, eps=0.5, min_samples=5)
        assert 'cluster_label' in df.columns
        assert metadata['n_clusters'] >= 0
        assert 'silhouette_score' in metadata

    def test_run_dbscan_noise_handling(self, sample_embedding):
        """Test that noise points are handled correctly."""
        df, metadata = run_dbscan(sample_embedding, eps=0.1, min_samples=10) # High min_samples to create noise
        noise_count = (df['cluster_label'] == -1).sum()
        assert noise_count >= 0

class TestFisherExactTest:
    def test_perform_fisher_exact_test_success(self, sample_embedding):
        """Test Fisher's exact test on a valid cluster."""
        # First, create a cluster
        df, _ = run_dbscan(sample_embedding, eps=1.0, min_samples=5)
        
        # Ensure we have a cluster to test
        unique_labels = df['cluster_label'].unique()
        if -1 in unique_labels:
            unique_labels = unique_labels[unique_labels != -1]
        
        if len(unique_labels) > 0:
            cluster_id = unique_labels[0]
            result = perform_fisher_exact_test(df, df, cluster_id)
            assert result['status'] in ['success', 'skipped']
            if result['status'] == 'success':
                assert 'p_value' in result
                assert 'odds_ratio' in result

    def test_perform_fisher_exact_test_noise_cluster(self, sample_embedding):
        """Test that noise clusters are skipped."""
        df, _ = run_dbscan(sample_embedding, eps=1.0, min_samples=5)
        result = perform_fisher_exact_test(df, df, -1)
        assert result['status'] == 'skipped'
        assert result['reason'] == 'Noise cluster'

class TestClusteringPipeline:
    @patch('src.analysis.clustering.load_umap_embedding')
    @patch('src.analysis.clustering.run_dbscan')
    @patch('src.analysis.clustering.perform_fisher_exact_test')
    @patch('src.analysis.clustering.run_label_permutation_test')
    @patch('src.analysis.clustering.save_clustering_results')
    def test_run_clustering_pipeline_mocked(self, mock_save, mock_perm, mock_fisher, mock_dbscan, mock_load):
        """Test the pipeline with mocked dependencies."""
        # Setup mocks
        mock_load.return_value = pd.DataFrame({'umap_1': [0, 1], 'umap_2': [0, 1], 'resistance_label': ['high', 'low']})
        mock_dbscan.return_value = (pd.DataFrame({'umap_1': [0, 1], 'umap_2': [0, 1], 'resistance_label': ['high', 'low'], 'cluster_label': [0, 0]}), {'n_clusters': 1})
        mock_fisher.return_value = {'status': 'success', 'p_value': 0.01, 'cluster_id': 0}
        mock_perm.return_value = [0.05, 0.06, 0.07]
        mock_save.return_value = Path('/tmp/test.json')

        output = run_clustering_pipeline(eps=0.5, min_samples=2, permutation_iterations=3)
        
        assert mock_load.called
        assert mock_dbscan.called
        assert mock_fisher.called
        assert mock_perm.called
        assert mock_save.called
        assert output == Path('/tmp/test.json')

    def test_save_clustering_results(self, temp_processed_dir):
        """Test saving clustering results to JSON."""
        results = [
            {'cluster_id': 0, 'status': 'success', 'p_value': 0.01},
            {'cluster_id': 1, 'status': 'success', 'p_value': 0.05}
        ]
        perm_p = [0.02, 0.03, 0.04]
        metadata = {'n_clusters': 2}
        
        output_path = save_clustering_results(results, perm_p, metadata, temp_processed_dir / "test_results.json")
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert 'metadata' in data
        assert 'clusters' in data
        assert 'permutation_test' in data
        assert len(data['clusters']) == 2
        assert len(data['permutation_test']['permuted_p_values']) == 3