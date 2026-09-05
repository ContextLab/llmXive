"""
Unit tests for network analysis edge cases.

Tests for:
- Disconnected networks (assigns 0 centrality)
- Empty networks (returns empty dicts)
- Missing gene overlaps (logs warning, skips)
"""
import pytest
import networkx as nx
from pathlib import Path
import json
import logging

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.network_analysis import (
    compute_degree_centrality,
    compute_eigenvector_centrality,
    compute_betweenness_centrality,
    compute_all_centrality_metrics,
    process_organism_networks
)
from code.network_analysis import NetworkAnalysisError

# Configure logging for tests
logging.basicConfig(level=logging.INFO)

class TestDisconnectedNetworks:
    """Tests for disconnected network handling."""
    
    def test_degree_centrality_disconnected(self):
        """Degree centrality should be 0 for isolated nodes."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3)])  # Component 1
        G.add_node(4)  # Isolated node
        G.add_edges_from([(5, 6)])  # Component 2
        
        centrality = compute_degree_centrality(G)
        
        # Nodes in components should have non-zero centrality
        assert centrality[1] > 0
        assert centrality[2] > 0
        assert centrality[3] > 0
        assert centrality[5] > 0
        assert centrality[6] > 0
        
        # Isolated node should have 0 centrality
        assert centrality[4] == 0.0
    
    def test_eigenvector_centrality_disconnected(self):
        """Eigenvector centrality should handle disconnected components."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3)])  # Component 1
        G.add_node(4)  # Isolated node
        
        centrality = compute_eigenvector_centrality(G)
        
        # Isolated node should have 0 centrality
        assert centrality[4] == 0.0
    
    def test_betweenness_centrality_disconnected(self):
        """Betweenness centrality should be 0 for isolated nodes."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3)])  # Component 1
        G.add_node(4)  # Isolated node
        
        centrality = compute_betweenness_centrality(G)
        
        # Isolated node should have 0 centrality
        assert centrality[4] == 0.0
    
    def test_all_centrality_disconnected(self):
        """All centrality metrics should handle disconnected graphs."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3)])  # Component 1
        G.add_node(4)  # Isolated node
        
        results = compute_all_centrality_metrics(G)
        
        # All metrics should have 0 for isolated node
        assert results['degree'][4] == 0.0
        assert results['eigenvector'][4] == 0.0
        assert results['betweenness'][4] == 0.0

class TestEmptyNetworks:
    """Tests for empty network handling."""
    
    def test_degree_centrality_empty(self):
        """Degree centrality should return empty dict for empty graph."""
        G = nx.Graph()
        
        centrality = compute_degree_centrality(G)
        assert centrality == {}
    
    def test_eigenvector_centrality_empty(self):
        """Eigenvector centrality should return empty dict for empty graph."""
        G = nx.Graph()
        
        centrality = compute_eigenvector_centrality(G)
        assert centrality == {}
    
    def test_betweenness_centrality_empty(self):
        """Betweenness centrality should return empty dict for empty graph."""
        G = nx.Graph()
        
        centrality = compute_betweenness_centrality(G)
        assert centrality == {}
    
    def test_all_centrality_empty(self):
        """All centrality metrics should return empty dicts for empty graph."""
        G = nx.Graph()
        
        results = compute_all_centrality_metrics(G)
        
        assert results['degree'] == {}
        assert results['eigenvector'] == {}
        assert results['betweenness'] == {}

class TestMissingOverlaps:
    """Tests for missing gene overlap handling."""
    
    def test_process_organism_no_network(self, tmp_path):
        """Should skip processing if no network data."""
        organism_data = {
            'organism_name': 'test_org',
            'adjacency_list': {},
            'essentiality_labels': {'gene1': 1, 'gene2': 0}
        }
        
        result = process_organism_networks(organism_data, tmp_path)
        
        assert result['status'] == 'skipped'
        assert result['reason'] == 'No network data'
    
    def test_process_organism_no_labels(self, tmp_path):
        """Should skip processing if no essentiality labels."""
        organism_data = {
            'organism_name': 'test_org',
            'adjacency_list': {'gene1': ['gene2'], 'gene2': ['gene1']},
            'essentiality_labels': {}
        }
        
        result = process_organism_networks(organism_data, tmp_path)
        
        assert result['status'] == 'skipped'
        assert result['reason'] == 'No essentiality labels'
    
    def test_process_organism_no_overlap(self, tmp_path, caplog):
        """Should skip processing if no gene overlap."""
        organism_data = {
            'organism_name': 'test_org',
            'adjacency_list': {'geneA': ['geneB'], 'geneB': ['geneA']},
            'essentiality_labels': {'geneX': 1, 'geneY': 0}
        }
        
        with caplog.at_level(logging.WARNING):
            result = process_organism_networks(organism_data, tmp_path)
        
        assert result['status'] == 'skipped'
        assert result['reason'] == 'No gene overlap'
        assert 'No gene overlap' in caplog.text
    
    def test_process_organism_partial_overlap(self, tmp_path):
        """Should process if there is partial overlap."""
        organism_data = {
            'organism_name': 'test_org',
            'adjacency_list': {
                'geneA': ['geneB', 'geneC'],
                'geneB': ['geneA'],
                'geneC': ['geneA']
            },
            'essentiality_labels': {
                'geneB': 1,
                'geneC': 0,
                'geneX': 1  # No overlap
            }
        }
        
        result = process_organism_networks(organism_data, tmp_path)
        
        assert result['status'] == 'success'
        assert result['overlap_count'] == 2  # geneB and geneC
        assert 'geneB' in result['centrality']['degree']
        assert 'geneC' in result['centrality']['degree']
        assert 'geneA' not in result['centrality']['degree']  # Not in labels
        assert 'geneX' not in result['centrality']['degree']  # Not in network

class TestSingleNodeNetworks:
    """Tests for single-node networks."""
    
    def test_single_node_degree(self):
        """Single node should have degree centrality 0."""
        G = nx.Graph()
        G.add_node(1)
        
        centrality = compute_degree_centrality(G)
        assert centrality[1] == 0.0
    
    def test_single_node_eigenvector(self):
        """Single node should have eigenvector centrality 0."""
        G = nx.Graph()
        G.add_node(1)
        
        centrality = compute_eigenvector_centrality(G)
        assert centrality[1] == 0.0
    
    def test_single_node_betweenness(self):
        """Single node should have betweenness centrality 0."""
        G = nx.Graph()
        G.add_node(1)
        
        centrality = compute_betweenness_centrality(G)
        assert centrality[1] == 0.0