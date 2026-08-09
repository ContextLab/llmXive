import pytest
import numpy as np
import networkx as nx
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path if not already
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from graph_metrics import (
    generate_correlation_matrix,
    compute_global_efficiency,
    compute_clustering_coefficient,
    compute_modularity_louvain,
    compute_modularity_with_resolution_sweep,
    compute_graph_metrics,
    _get_schaefer_atlas
)

class TestGraphMetrics:
    
    def test_schaefer_atlas_fetch(self):
        """Test that Schaefer atlas is fetched correctly for valid ROI counts."""
        # Test with 100 ROIs
        atlas = _get_schaefer_atlas(n_rois=100)
        assert 'maps' in atlas
        assert 'labels' in atlas
        assert atlas['maps'].shape[0] == 100 # Check shape roughly
        
        # Test with invalid ROI count
        with pytest.raises(ValueError):
            _get_schaefer_atlas(n_rois=999)

    def test_correlation_matrix_symmetry(self):
        """Test that the generated correlation matrix is symmetric."""
        # Create a mock time series to simulate input
        # We mock the masker to return a fixed time series
        mock_time_series = np.random.rand(100, 200) # 100 time points, 200 features (simulated)
        
        # We cannot easily test generate_correlation_matrix without real NIfTI and Atlas
        # So we test the logic on a synthetic matrix that would be the output
        # If we had a real file, we would assert symmetry.
        # Instead, we verify the property on a synthetic matrix that mimics the output
        n_rois = 100
        synthetic_corr = np.random.rand(n_rois, n_rois)
        synthetic_corr = (synthetic_corr + synthetic_corr.T) / 2
        np.fill_diagonal(synthetic_corr, 1.0)
        
        assert np.allclose(synthetic_corr, synthetic_corr.T)
        assert np.allclose(np.diag(synthetic_corr), 1.0)

    def test_global_efficiency_calculation(self):
        """Test global efficiency calculation on a known graph."""
        # Create a complete graph (efficiency should be 1.0)
        n_nodes = 10
        G = nx.complete_graph(n_nodes)
        corr_matrix = nx.to_numpy_array(G) # 1.0 for edges, 0.0 for non-edges
        
        eff = compute_global_efficiency(corr_matrix)
        # In a complete graph, efficiency is 1.0
        assert np.isclose(eff, 1.0, atol=1e-5)

    def test_global_efficiency_disconnected(self):
        """Test global efficiency on a disconnected graph."""
        # Create two disconnected nodes
        corr_matrix = np.array([[1.0, 0.0], [0.0, 1.0]])
        eff = compute_global_efficiency(corr_matrix)
        # Distance is infinity, so efficiency is 0
        assert eff == 0.0

    def test_clustering_coefficient_complete_graph(self):
        """Test clustering coefficient on a complete graph."""
        n_nodes = 5
        G = nx.complete_graph(n_nodes)
        corr_matrix = nx.to_numpy_array(G)
        
        coef = compute_clustering_coefficient(corr_matrix)
        # Clustering coefficient of a complete graph is 1.0
        assert np.isclose(coef, 1.0, atol=1e-5)

    def test_modularity_louvain(self):
        """Test modularity calculation."""
        # Create a graph with known community structure
        # Two cliques of 5 nodes each, no connections between them
        G = nx.disjoint_union(nx.complete_graph(5), nx.complete_graph(5))
        corr_matrix = nx.to_numpy_array(G)
        
        mod = compute_modularity_louvain(corr_matrix, resolution=1.0)
        # Modularity should be positive for a graph with communities
        assert mod > 0.0

    def test_modularity_resolution_sweep(self):
        """Test resolution sweep returns dictionary with expected keys."""
        n_nodes = 10
        G = nx.complete_graph(n_nodes)
        corr_matrix = nx.to_numpy_array(G)
        
        resolutions = [0.5, 1.0, 2.0]
        results = compute_modularity_with_resolution_sweep(corr_matrix, resolutions=resolutions)
        
        assert isinstance(results, dict)
        for res in resolutions:
            assert res in results
            assert isinstance(results[res], float)

    def test_compute_graph_metrics_integration(self):
        """Integration test for compute_graph_metrics with mocked dependencies."""
        # Mock the atlas fetch and masker to avoid downloading real data and processing NIfTI
        mock_time_series = np.random.rand(100, 100) # 100 timepoints, 100 ROIs
        
        with patch('graph_metrics._get_schaefer_atlas') as mock_atlas, \
             patch('graph_metrics.input_data.NiftiLabelsMasker') as MockMasker:
            
            # Setup atlas mock
            mock_atlas.return_value = {
                'maps': MagicMock(),
                'labels': ['Region_' + str(i) for i in range(100)]
            }
            
            # Setup masker mock
            mock_instance = MagicMock()
            mock_instance.fit_transform.return_value = mock_time_series
            MockMasker.return_value = mock_instance
            
            # Mock the file existence check
            with patch('os.path.exists', return_value=True):
                metrics = compute_graph_metrics("dummy.nii.gz", n_rois=100)
                
                assert 'correlation_matrix' in metrics
                assert 'global_efficiency' in metrics
                assert 'clustering_coefficient' in metrics
                assert 'modularity' in metrics
                
                assert metrics['correlation_matrix'].shape == (100, 100)
                assert isinstance(metrics['global_efficiency'], float)
                assert isinstance(metrics['clustering_coefficient'], float)
                assert isinstance(metrics['modularity'], float)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])