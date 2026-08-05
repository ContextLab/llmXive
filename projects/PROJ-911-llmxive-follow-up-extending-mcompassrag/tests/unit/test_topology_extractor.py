"""
Unit tests for topology_extractor module.

Tests cover:
- calculate_topological_metrics for various graph sizes
- extract_features_for_retrieved_docs filtering logic
- Edge cases (empty graphs, disconnected graphs)
"""
import pytest
import networkx as nx
from pathlib import Path
import tempfile
import json
import csv
import sys
import os

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.topology_extractor import (
    calculate_topological_metrics,
    extract_features_for_retrieved_docs,
    save_retrieved_features,
    load_graphs
)


class TestCalculateTopologicalMetrics:
    """Tests for calculate_topological_metrics function."""

    def test_empty_graph(self):
        """Test metrics for an empty graph."""
        G = nx.Graph()
        metrics = calculate_topological_metrics(G)
        
        assert metrics['modularity'] == 0.0
        assert metrics['average_path_length'] == 0.0
        assert metrics['average_degree'] == 0.0
        assert metrics['average_betweenness_centrality'] == 0.0

    def test_single_node(self):
        """Test metrics for a single node graph."""
        G = nx.Graph()
        G.add_node('A')
        metrics = calculate_topological_metrics(G)
        
        assert metrics['modularity'] == 0.0
        assert metrics['average_path_length'] == 0.0
        assert metrics['average_degree'] == 0.0
        assert metrics['average_betweenness_centrality'] == 0.0

    def test_connected_graph(self):
        """Test metrics for a simple connected graph."""
        G = nx.Graph()
        G.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'D')])
        metrics = calculate_topological_metrics(G)
        
        # Average degree should be 2 * edges / nodes = 6 / 4 = 1.5
        assert metrics['average_degree'] == 1.5
        # Modularity should be > 0 if communities detected
        assert metrics['modularity'] >= 0.0
        # Average path length should be finite
        assert metrics['average_path_length'] > 0.0

    def test_disconnected_graph(self):
        """Test metrics for a disconnected graph."""
        G = nx.Graph()
        G.add_edges_from([('A', 'B'), ('C', 'D')])
        metrics = calculate_topological_metrics(G)
        
        # Average degree should be 1.0 (2 edges * 2 / 4 nodes)
        assert metrics['average_degree'] == 1.0
        # Should not raise error
        assert isinstance(metrics['average_path_length'], float)
        assert metrics['average_path_length'] >= 0.0

    def test_complete_graph(self):
        """Test metrics for a complete graph (K4)."""
        G = nx.complete_graph(4)
        metrics = calculate_topological_metrics(G)
        
        # Average degree should be n-1 = 3
        assert metrics['average_degree'] == 3.0
        # Average path length should be 1.0
        assert metrics['average_path_length'] == 1.0


class TestExtractFeaturesForRetrievedDocs:
    """Tests for extract_features_for_retrieved_docs function."""

    def test_filtering_retrieved_only(self):
        """Test that only retrieved documents are included."""
        # Create sample graphs
        graphs = {
            'doc1': nx.complete_graph(3),
            'doc2': nx.complete_graph(3),
            'doc3': nx.complete_graph(3),
            'doc4': nx.complete_graph(3)
        }
        
        # Only retrieve doc1 and doc3
        retrieved_ids = ['doc1', 'doc3']
        
        features = extract_features_for_retrieved_docs(graphs, retrieved_ids)
        
        # Should only have 2 features
        assert len(features) == 2
        # Should contain only doc1 and doc3
        doc_ids = [f['doc_id'] for f in features]
        assert 'doc1' in doc_ids
        assert 'doc3' in doc_ids
        assert 'doc2' not in doc_ids
        assert 'doc4' not in doc_ids

    def test_missing_graphs(self):
        """Test handling of missing graph data for retrieved docs."""
        graphs = {
            'doc1': nx.complete_graph(3),
            'doc2': nx.complete_graph(3)
        }
        
        # Request doc1 (exists) and doc99 (missing)
        retrieved_ids = ['doc1', 'doc99']
        
        features = extract_features_for_retrieved_docs(graphs, retrieved_ids)
        
        # Should only have doc1
        assert len(features) == 1
        assert features[0]['doc_id'] == 'doc1'

    def test_empty_retrieved_list(self):
        """Test with empty retrieved list."""
        graphs = {'doc1': nx.complete_graph(3)}
        retrieved_ids = []
        
        features = extract_features_for_retrieved_docs(graphs, retrieved_ids)
        
        assert len(features) == 0


class TestSaveRetrievedFeatures:
    """Tests for save_retrieved_features function."""

    def test_save_to_file(self):
        """Test saving features to a CSV file."""
        features = [
            {'doc_id': 'doc1', 'modularity': 0.5, 'average_path_length': 2.0},
            {'doc_id': 'doc2', 'modularity': 0.3, 'average_path_length': 1.5}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = Path(f.name)
        
        try:
            save_retrieved_features(features, temp_path)
            
            # Check file exists and content
            assert temp_path.exists()
            
            with open(temp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 2
            assert rows[0]['doc_id'] == 'doc1'
            assert float(rows[0]['modularity']) == 0.5
        finally:
            temp_path.unlink()

    def test_empty_features(self):
        """Test saving empty features list."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = Path(f.name)
        
        try:
            save_retrieved_features([], temp_path)
            # Should not raise, file might be empty or not created
            # Depending on implementation, we just ensure no crash
        finally:
            if temp_path.exists():
                temp_path.unlink()