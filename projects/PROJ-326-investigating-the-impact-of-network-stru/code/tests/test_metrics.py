"""
Unit tests for metric extraction logic in code/src/generators/metrics.py
"""

import json
import os
import tempfile
from pathlib import Path

import networkx as nx
import numpy as np
import pytest

from code.src.generators.metrics import (
    compute_degree_distribution,
    compute_clustering_metrics,
    compute_path_length_metrics,
    extract_all_metrics,
    update_manifest,
    load_manifest,
    MANIFEST_PATH
)

class TestDegreeDistribution:
    """Tests for degree distribution computation."""
    
    def test_empty_graph(self):
        """Test degree distribution on an empty graph."""
        G = nx.empty_graph(0)
        result = compute_degree_distribution(G)
        
        assert result['degrees'] == []
        assert result['mean'] == 0.0
        assert result['std'] == 0.0
        assert result['max'] == 0
        assert result['min'] == 0
        assert result['histogram'] == {}
    
    def test_single_node(self):
        """Test degree distribution on a single node graph."""
        G = nx.empty_graph(1)
        result = compute_degree_distribution(G)
        
        assert result['degrees'] == [0]
        assert result['mean'] == 0.0
        assert result['std'] == 0.0
        assert result['max'] == 0
        assert result['min'] == 0
    
    def test_complete_graph(self):
        """Test degree distribution on a complete graph."""
        n = 5
        G = nx.complete_graph(n)
        result = compute_degree_distribution(G)
        
        expected_degree = n - 1
        assert len(result['degrees']) == n
        assert all(d == expected_degree for d in result['degrees'])
        assert result['mean'] == expected_degree
        assert result['std'] == 0.0
        assert result['max'] == expected_degree
        assert result['min'] == expected_degree
        assert result['histogram'] == {expected_degree: n}
    
    def test_star_graph(self):
        """Test degree distribution on a star graph."""
        n = 5
        G = nx.star_graph(n)  # n+1 nodes total
        result = compute_degree_distribution(G)
        
        # Center node has degree n, leaves have degree 1
        assert result['max'] == n
        assert result['min'] == 1
        assert result['histogram'][n] == 1
        assert result['histogram'][1] == n

class TestClusteringMetrics:
    """Tests for clustering coefficient computation."""
    
    def test_empty_graph(self):
        """Test clustering on an empty graph."""
        G = nx.empty_graph(0)
        result = compute_clustering_metrics(G)
        
        assert result['local'] == {}
        assert result['global'] == 0.0
        assert result['distribution'] == {}
    
    def test_complete_graph(self):
        """Test clustering on a complete graph (should be 1.0)."""
        G = nx.complete_graph(5)
        result = compute_clustering_metrics(G)
        
        assert result['global'] == 1.0
        assert all(v == 1.0 for v in result['local'].values())
    
    def test_path_graph(self):
        """Test clustering on a path graph (should be 0.0)."""
        G = nx.path_graph(5)
        result = compute_clustering_metrics(G)
        
        assert result['global'] == 0.0
        assert all(v == 0.0 for v in result['local'].values())
    
    def test_watts_strogatz(self):
        """Test clustering on a Watts-Strogatz small-world graph."""
        G = nx.watts_strogatz_graph(100, 4, 0.1, seed=42)
        result = compute_clustering_metrics(G)
        
        # Small-world graphs should have high clustering
        assert result['global'] > 0.3  # Typical for small-world
        assert len(result['local']) == 100

class TestPathLengthMetrics:
    """Tests for path length computation."""
    
    def test_disconnected_graph(self):
        """Test path length on a disconnected graph."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])  # Two components
        result = compute_path_length_metrics(G)
        
        assert result['is_connected'] is False
        assert result['average_path_length'] is None
        assert result['diameter'] is None
    
    def test_single_node(self):
        """Test path length on a single node graph."""
        G = nx.empty_graph(1)
        result = compute_path_length_metrics(G)
        
        assert result['is_connected'] is True
        assert result['average_path_length'] == 0.0
        assert result['diameter'] == 0
    
    def test_path_graph(self):
        """Test path length on a path graph."""
        G = nx.path_graph(5)
        result = compute_path_length_metrics(G)
        
        assert result['is_connected'] is True
        assert result['diameter'] == 4
        # Average path length for path graph of n nodes is (n+1)/3
        expected_avg = (5 + 1) / 3.0
        assert abs(result['average_path_length'] - expected_avg) < 0.1

class TestExtractAllMetrics:
    """Tests for the main metric extraction function."""
    
    def test_erdos_renyi(self):
        """Test extraction on an Erdős-Rényi graph."""
        G = nx.erdos_renyi_graph(100, 0.1, seed=42)
        metrics = extract_all_metrics(G, "test_er", "erdos_renyi", {"p": 0.1})
        
        assert metrics['graph_id'] == "test_er"
        assert metrics['graph_type'] == "erdos_renyi"
        assert metrics['node_count'] == 100
        assert 'degree_distribution' in metrics
        assert 'clustering_metrics' in metrics
        assert 'path_length_metrics' in metrics
        assert metrics['generation_parameters'] == {"p": 0.1}
    
    def test_structure_consistency(self):
        """Test that all expected fields are present."""
        G = nx.watts_strogatz_graph(50, 4, 0.1, seed=42)
        metrics = extract_all_metrics(G, "test_sw", "watts_strogatz")
        
        required_fields = [
            'graph_id', 'graph_type', 'node_count', 'edge_count',
            'degree_distribution', 'clustering_metrics', 
            'path_length_metrics', 'generation_parameters'
        ]
        
        for field in required_fields:
            assert field in metrics, f"Missing field: {field}"

class TestManifestIO:
    """Tests for manifest file I/O."""
    
    @pytest.fixture
    def temp_manifest_path(self):
        """Create a temporary manifest path for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test_manifest.json"
    
    def test_create_new_manifest(self, temp_manifest_path):
        """Test creating a new manifest file."""
        metrics = extract_all_metrics(nx.path_graph(10), "test1", "path")
        update_manifest([metrics], temp_manifest_path)
        
        assert temp_manifest_path.exists()
        
        manifest = load_manifest(temp_manifest_path)
        assert len(manifest['graphs']) == 1
        assert manifest['graphs'][0]['graph_id'] == "test1"
    
    def test_append_to_manifest(self, temp_manifest_path):
        """Test appending to an existing manifest."""
        metrics1 = extract_all_metrics(nx.path_graph(10), "test1", "path")
        metrics2 = extract_all_metrics(nx.path_graph(20), "test2", "path")
        
        update_manifest([metrics1], temp_manifest_path)
        update_manifest([metrics2], temp_manifest_path)
        
        manifest = load_manifest(temp_manifest_path)
        assert len(manifest['graphs']) == 2
    
    def test_update_summary(self, temp_manifest_path):
        """Test that summary statistics are updated correctly."""
        metrics1 = extract_all_metrics(nx.complete_graph(10), "test1", "complete")
        metrics2 = extract_all_metrics(nx.path_graph(10), "test2", "path")
        
        update_manifest([metrics1, metrics2], temp_manifest_path)
        
        manifest = load_manifest(temp_manifest_path)
        summary = manifest['summary']
        
        assert summary['total_graphs'] == 2
        assert summary['by_type']['complete'] == 1
        assert summary['by_type']['path'] == 1
        assert summary['avg_clustering'] is not None
        assert summary['avg_path_length'] is not None
    
    def test_load_nonexistent_manifest(self, temp_manifest_path):
        """Test loading a manifest that doesn't exist."""
        manifest = load_manifest(temp_manifest_path)
        
        assert manifest == {'graphs': [], 'summary': {}}

class TestIntegration:
    """Integration tests for the metrics module."""
    
    def test_batch_extraction(self):
        """Test extracting metrics for multiple graphs."""
        graphs = [
            nx.erdos_renyi_graph(50, 0.1, seed=42),
            nx.watts_strogatz_graph(50, 4, 0.1, seed=42),
            nx.barabasi_albert_graph(50, 2, seed=42)
        ]
        
        metrics_list = []
        for i, G in enumerate(graphs):
            metrics = extract_all_metrics(
                G, 
                f"graph_{i}", 
                ["erdos_renyi", "watts_strogatz", "barabasi_albert"][i]
            )
            metrics_list.append(metrics)
        
        assert len(metrics_list) == 3
        assert all(m['node_count'] == 50 for m in metrics_list)
        
        # Verify different clustering coefficients
        clusterings = [m['clustering_metrics']['global'] for m in metrics_list]
        assert len(set(round(c, 2) for c in clusterings)) >= 2  # At least 2 different values
    
    def test_manifest_persistence(self, temp_manifest_path):
        """Test that manifest data persists across reads."""
        metrics = extract_all_metrics(nx.path_graph(10), "test", "path")
        update_manifest([metrics], temp_manifest_path)
        
        # Read back and verify
        manifest1 = load_manifest(temp_manifest_path)
        
        # Modify and write again
        metrics2 = extract_all_metrics(nx.path_graph(20), "test2", "path")
        update_manifest([metrics2], temp_manifest_path)
        
        manifest2 = load_manifest(temp_manifest_path)
        
        assert len(manifest2['graphs']) == 2
        assert manifest2['graphs'][0]['graph_id'] == "test"
        assert manifest2['graphs'][1]['graph_id'] == "test2"