"""
Unit tests for code/preprocess/structural.py graph metric calculation.

Tests cover:
- Global efficiency calculation
- Clustering coefficient calculation
- Modularity calculation
- Sparsity threshold handling
- Empty/low-density graph handling
"""
import numpy as np
import networkx as nx
import pytest
import sys
import os
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocess.structural import calculate_graph_metrics

class TestCalculateGraphMetrics:
    """Tests for calculate_graph_metrics function."""
    
    def test_global_efficiency_complete_graph(self):
        """Test global efficiency on a complete graph (should be close to 1.0)."""
        # Create a 5x5 complete graph adjacency matrix
        n = 5
        adj_matrix = np.ones((n, n))
        np.fill_diagonal(adj_matrix, 0)  # No self-loops
        
        # Threshold should keep all edges (density=1.0, but we use top X%)
        metrics = calculate_graph_metrics(adj_matrix, threshold=1.0)
        
        assert 'global_efficiency' in metrics
        assert 'clustering_coefficient' in metrics
        assert 'modularity' in metrics
        assert metrics['sparsity'] == 0.0  # Complete graph has 0 sparsity
        assert metrics['n_nodes'] == n
        assert metrics['n_edges'] == n * (n - 1) / 2
        
        # Global efficiency of complete graph should be 1.0
        assert abs(metrics['global_efficiency'] - 1.0) < 1e-6
    
    def test_clustering_coefficient_ring_graph(self):
        """Test clustering coefficient on a ring graph (known value)."""
        # Create a ring graph adjacency matrix
        n = 6
        adj_matrix = np.zeros((n, n))
        for i in range(n):
            adj_matrix[i, (i + 1) % n] = 1
            adj_matrix[(i + 1) % n, i] = 1
        
        metrics = calculate_graph_metrics(adj_matrix, threshold=1.0)
        
        # Ring graph clustering coefficient should be 0.5
        assert abs(metrics['clustering_coefficient'] - 0.5) < 0.01
    
    def test_modularity_community_graph(self):
        """Test modularity on a graph with clear communities."""
        # Create two disconnected cliques (perfect modularity)
        n = 4
        adj_matrix = np.zeros((2 * n, 2 * n))
        
        # First clique
        for i in range(n):
            for j in range(n):
                if i != j:
                    adj_matrix[i, j] = 1
        
        # Second clique
        for i in range(n, 2 * n):
            for j in range(n, 2 * n):
                if i != j:
                    adj_matrix[i, j] = 1
        
        metrics = calculate_graph_metrics(adj_matrix, threshold=1.0)
        
        assert 'modularity' in metrics
        # Modularity should be high for clearly separated communities
        assert metrics['modularity'] > 0.5
    
    def test_sparsity_calculation(self):
        """Test that sparsity is correctly calculated as 1 - density."""
        n = 4
        # Create a graph with 2 edges out of 6 possible
        adj_matrix = np.zeros((n, n))
        adj_matrix[0, 1] = 1
        adj_matrix[1, 0] = 1
        adj_matrix[2, 3] = 1
        adj_matrix[3, 2] = 1
        
        metrics = calculate_graph_metrics(adj_matrix, threshold=1.0)
        
        # Density = 2/6 = 0.333..., Sparsity = 1 - 0.333... = 0.666...
        expected_density = 2 / 6
        expected_sparsity = 1 - expected_density
        
        assert abs(metrics['density'] - expected_density) < 1e-6
        assert abs(metrics['sparsity'] - expected_sparsity) < 1e-6
    
    def test_threshold_density_based(self):
        """Test density-based thresholding keeps top X% edges."""
        n = 4
        # Create weighted adjacency matrix
        adj_matrix = np.zeros((n, n))
        adj_matrix[0, 1] = 0.9
        adj_matrix[1, 0] = 0.9
        adj_matrix[0, 2] = 0.5
        adj_matrix[2, 0] = 0.5
        adj_matrix[0, 3] = 0.1
        adj_matrix[3, 0] = 0.1
        
        # Keep top 50% of edges (density=0.5)
        metrics = calculate_graph_metrics(adj_matrix, threshold=0.5)
        
        # Should keep only the strongest edge (0.9)
        assert metrics['n_edges'] == 1
        assert metrics['density'] == 1 / (n * (n - 1) / 2)  # 1/6
    
    def test_empty_graph_handling(self):
        """Test handling of completely empty graph."""
        n = 4
        adj_matrix = np.zeros((n, n))
        
        metrics = calculate_graph_metrics(adj_matrix, threshold=1.0)
        
        # Should return 0 for all metrics
        assert metrics['global_efficiency'] == 0
        assert metrics['clustering_coefficient'] == 0
        assert metrics['modularity'] == 0
        assert metrics['sparsity'] == 1.0
    
    def test_sparse_graph_exclusion_threshold(self):
        """Test that sparse graphs are handled (sparsity > 90% exclusion)."""
        n = 10
        # Create a very sparse graph (only 1 edge)
        adj_matrix = np.zeros((n, n))
        adj_matrix[0, 1] = 1
        adj_matrix[1, 0] = 1
        
        metrics = calculate_graph_metrics(adj_matrix, threshold=1.0)
        
        # Sparsity should be very high (close to 1.0)
        assert metrics['sparsity'] > 0.9
        # Metrics should still be calculated (exclusion is handled by caller)
        assert metrics['n_nodes'] == n
        assert metrics['n_edges'] == 1
    
    def test_weighted_to_binary_conversion(self):
        """Test that weighted matrices are correctly converted to binary."""
        n = 3
        adj_matrix = np.array([
            [0, 0.8, 0.2],
            [0.8, 0, 0.5],
            [0.2, 0.5, 0]
        ])
        
        # With threshold=0.5, should keep edges >= 0.5
        metrics = calculate_graph_metrics(adj_matrix, threshold=0.5)
        
        # Should have 2 edges (0.8 and 0.5)
        assert metrics['n_edges'] == 2
    
    def test_return_dict_structure(self):
        """Test that return dictionary has all required keys."""
        n = 3
        adj_matrix = np.ones((n, n))
        np.fill_diagonal(adj_matrix, 0)
        
        metrics = calculate_graph_metrics(adj_matrix, threshold=1.0)
        
        required_keys = [
            'sparsity', 'density', 'global_efficiency',
            'clustering_coefficient', 'modularity',
            'n_nodes', 'n_edges'
        ]
        
        for key in required_keys:
            assert key in metrics, f"Missing key: {key}"
    
    def test_symmetric_matrix_handling(self):
        """Test that symmetric adjacency matrices are handled correctly."""
        n = 4
        # Create symmetric matrix
        adj_matrix = np.array([
            [0, 1, 1, 0],
            [1, 0, 1, 1],
            [1, 1, 0, 0],
            [0, 1, 0, 0]
        ], dtype=float)
        
        metrics = calculate_graph_metrics(adj_matrix, threshold=1.0)
        
        # Should calculate metrics without error
        assert metrics['n_nodes'] == n
        assert metrics['global_efficiency'] >= 0
        assert metrics['clustering_coefficient'] >= 0
    
    def test_different_threshold_values(self):
        """Test behavior with different threshold values."""
        n = 5
        adj_matrix = np.random.rand(n, n)
        adj_matrix = (adj_matrix + adj_matrix.T) / 2
        np.fill_diagonal(adj_matrix, 0)
        
        # Test with various thresholds
        for threshold in [0.1, 0.25, 0.5, 0.75]:
            metrics = calculate_graph_metrics(adj_matrix, threshold=threshold)
            assert metrics['density'] <= threshold + 0.01  # Allow small floating point error
            assert metrics['sparsity'] >= 1 - threshold - 0.01
    
    def test_large_graph_performance(self):
        """Test that metrics can be calculated on a moderately large graph."""
        n = 20
        adj_matrix = np.random.rand(n, n)
        adj_matrix = (adj_matrix + adj_matrix.T) / 2
        np.fill_diagonal(adj_matrix, 0)
        # Make it sparse
        adj_matrix[adj_matrix < 0.3] = 0
        
        # Should complete without timeout or error
        metrics = calculate_graph_metrics(adj_matrix, threshold=0.1)
        
        assert metrics['n_nodes'] == n
        assert 'global_efficiency' in metrics
        assert 'modularity' in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])