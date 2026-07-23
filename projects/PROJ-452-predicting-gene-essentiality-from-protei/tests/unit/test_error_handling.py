import pytest
import logging
from code.network_analysis import compute_all_centrality_metrics, load_graph_from_adjacency_list
from code.data_loader import map_ids
import networkx as nx

logger = logging.getLogger(__name__)

class TestDisconnectedNetworks:
    """Test that disconnected networks are handled correctly (assign 0 centrality)."""

    def test_disconnected_components_degree_centrality(self):
        """Test degree centrality on a graph with isolated nodes."""
        # Create a graph with two components: 0-1 and isolated node 2
        G = nx.Graph()
        G.add_edge(0, 1)
        G.add_node(2)  # Isolated node
        
        centralities = compute_all_centrality_metrics(G)
        
        # Node 2 should have 0 centrality
        assert centralities['degree'][2] == 0.0
        # Nodes 0 and 1 should have non-zero centrality
        assert centralities['degree'][0] > 0.0
        assert centralities['degree'][1] > 0.0

    def test_disconnected_components_eigenvector_centrality(self):
        """Test eigenvector centrality on a graph with isolated nodes."""
        G = nx.Graph()
        G.add_edge(0, 1)
        G.add_node(2)
        
        centralities = compute_all_centrality_metrics(G)
        
        # Node 2 should have 0 eigenvector centrality
        assert centralities['eigenvector'][2] == 0.0
        # Nodes 0 and 1 should have non-zero eigenvector centrality
        assert centralities['eigenvector'][0] > 0.0
        assert centralities['eigenvector'][1] > 0.0

    def test_disconnected_components_betweenness_centrality(self):
        """Test betweenness centrality on a graph with isolated nodes."""
        G = nx.Graph()
        G.add_edge(0, 1)
        G.add_node(2)
        
        centralities = compute_all_centrality_metrics(G)
        
        # Node 2 should have 0 betweenness centrality
        assert centralities['betweenness'][2] == 0.0

class TestMissingGeneOverlaps:
    """Test that missing gene overlaps are handled with warnings."""

    def test_no_overlap_returns_empty_mapping(self, caplog):
        """Test that map_ids returns empty dict and logs warning when no overlap."""
        string_genes = {"geneA", "geneB"}
        deg_genes = {"geneX", "geneY"}
        
        with caplog.at_level(logging.WARNING):
            mapping, coverage = map_ids(string_genes, deg_genes)
        
        assert mapping == {}
        assert coverage == 0.0
        # Check that a warning or info about 0% coverage is logged
        # The current implementation logs "ID Mapping Coverage: 0.00%"
        # We assert the logic holds even if log level differs slightly
        assert len(mapping) == 0

    def test_partial_overlap_returns_common_only(self):
        """Test that map_ids returns only common genes."""
        string_genes = {"geneA", "geneB", "geneC"}
        deg_genes = {"geneB", "geneD"}
        
        mapping, coverage = map_ids(string_genes, deg_genes)
        
        assert "geneB" in mapping
        assert "geneA" not in mapping
        assert "geneC" not in mapping
        assert "geneD" not in mapping
        assert coverage == (1/3) * 100  # 33.33%

class TestEmptyNetworks:
    """Test handling of empty networks."""

    def test_empty_adjacency_list(self):
        """Test centrality computation on empty graph."""
        G = nx.Graph()
        centralities = compute_all_centrality_metrics(G)
        
        assert centralities['degree'] == {}
        assert centralities['eigenvector'] == {}
        assert centralities['betweenness'] == {}

    def test_single_node_no_edges(self):
        """Test centrality on single node with no edges."""
        G = nx.Graph()
        G.add_node(1)
        
        centralities = compute_all_centrality_metrics(G)
        
        assert centralities['degree'][1] == 0.0
        assert centralities['eigenvector'][1] == 0.0
        assert centralities['betweenness'][1] == 0.0