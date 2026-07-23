"""
Unit tests for feature extraction logic in compute_features.py.

Tests:
- bottleneck_resolution_ratio calculation
- branching_entropy calculation
- Graceful handling of nodes with 0 outgoing edges
"""
import os
import sys
import math
import pytest
from collections import Counter
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import networkx as nx
from code.data.compute_features import (
    compute_bottleneck_resolution_ratio,
    compute_branching_entropy,
    compute_features_for_node,
    compute_features_dataframe
)

@pytest.fixture
def sample_graph():
    """Create a sample directed graph for testing."""
    G = nx.DiGraph()
    
    # Add nodes
    G.add_node("A")
    G.add_node("B")
    G.add_node("C")
    G.add_node("D")
    G.add_node("E")
    
    # Add edges with types
    # Node A: 2 improves, 1 replaces, 1 extends (total 4) -> ratio = (2+1)/4 = 0.75
    G.add_edge("A", "B", type="improves")
    G.add_edge("A", "C", type="improves")
    G.add_edge("A", "D", type="replaces")
    G.add_edge("A", "E", type="extends")
    
    # Node B: 1 improves, 1 extends (total 2) -> ratio = 1/2 = 0.5
    G.add_edge("B", "C", type="improves")
    G.add_edge("B", "D", type="extends")
    
    # Node C: 1 replaces (total 1) -> ratio = 1/1 = 1.0
    G.add_edge("C", "D", type="replaces")
    
    # Node D: 0 outgoing edges
    
    # Node E: 2 replaces (total 2) -> ratio = 2/2 = 1.0
    G.add_edge("E", "C", type="replaces")
    G.add_edge("E", "D", type="replaces")
    
    return G

class TestBottleneckResolutionRatio:
    """Tests for compute_bottleneck_resolution_ratio function."""
    
    def test_ratio_calculation_node_a(self, sample_graph):
        """Test ratio calculation for node A: (2 improves + 1 replaces) / 4 total = 0.75"""
        ratio = compute_bottleneck_resolution_ratio(sample_graph, "A")
        assert ratio == 0.75, f"Expected 0.75, got {ratio}"
    
    def test_ratio_calculation_node_b(self, sample_graph):
        """Test ratio calculation for node B: (1 improves + 0 replaces) / 2 total = 0.5"""
        ratio = compute_bottleneck_resolution_ratio(sample_graph, "B")
        assert ratio == 0.5, f"Expected 0.5, got {ratio}"
    
    def test_ratio_calculation_node_c(self, sample_graph):
        """Test ratio calculation for node C: (0 improves + 1 replaces) / 1 total = 1.0"""
        ratio = compute_bottleneck_resolution_ratio(sample_graph, "C")
        assert ratio == 1.0, f"Expected 1.0, got {ratio}"
    
    def test_ratio_calculation_node_d_no_outgoing(self, sample_graph):
        """Test ratio for node D with 0 outgoing edges: should return 0.0"""
        ratio = compute_bottleneck_resolution_ratio(sample_graph, "D")
        assert ratio == 0.0, f"Expected 0.0, got {ratio}"
    
    def test_ratio_calculation_node_e(self, sample_graph):
        """Test ratio calculation for node E: (0 improves + 2 replaces) / 2 total = 1.0"""
        ratio = compute_bottleneck_resolution_ratio(sample_graph, "E")
        assert ratio == 1.0, f"Expected 1.0, got {ratio}"
    
    def test_nonexistent_node(self, sample_graph):
        """Test ratio for a node that doesn't exist in the graph."""
        ratio = compute_bottleneck_resolution_ratio(sample_graph, "Z")
        assert ratio == 0.0, f"Expected 0.0 for nonexistent node, got {ratio}"

class TestBranchingEntropy:
    """Tests for compute_branching_entropy function."""
    
    def test_entropy_calculation_node_a(self, sample_graph):
        """
        Test entropy for node A:
        Types: improves(2), replaces(1), extends(1) -> total 4
        Probabilities: 0.5, 0.25, 0.25
        Entropy = -(0.5*log2(0.5) + 0.25*log2(0.25) + 0.25*log2(0.25))
               = -(0.5*(-1) + 0.25*(-2) + 0.25*(-2))
               = -(-0.5 - 0.5 - 0.5) = 1.5
        """
        entropy = compute_branching_entropy(sample_graph, "A")
        expected = 1.5
        assert math.isclose(entropy, expected, rel_tol=1e-9), f"Expected {expected}, got {entropy}"
    
    def test_entropy_calculation_node_b(self, sample_graph):
        """
        Test entropy for node B:
        Types: improves(1), extends(1) -> total 2
        Probabilities: 0.5, 0.5
        Entropy = -(0.5*log2(0.5) + 0.5*log2(0.5)) = 1.0
        """
        entropy = compute_branching_entropy(sample_graph, "B")
        expected = 1.0
        assert math.isclose(entropy, expected, rel_tol=1e-9), f"Expected {expected}, got {entropy}"
    
    def test_entropy_calculation_node_c(self, sample_graph):
        """
        Test entropy for node C:
        Types: replaces(1) -> total 1
        Only one type -> entropy = 0.0
        """
        entropy = compute_branching_entropy(sample_graph, "C")
        assert entropy == 0.0, f"Expected 0.0, got {entropy}"
    
    def test_entropy_calculation_node_d_no_outgoing(self, sample_graph):
        """Test entropy for node D with 0 outgoing edges: should return 0.0"""
        entropy = compute_branching_entropy(sample_graph, "D")
        assert entropy == 0.0, f"Expected 0.0, got {entropy}"
    
    def test_entropy_calculation_node_e(self, sample_graph):
        """
        Test entropy for node E:
        Types: replaces(2) -> total 2
        Only one type -> entropy = 0.0
        """
        entropy = compute_branching_entropy(sample_graph, "E")
        assert entropy == 0.0, f"Expected 0.0, got {entropy}"
    
    def test_nonexistent_node(self, sample_graph):
        """Test entropy for a node that doesn't exist in the graph."""
        entropy = compute_branching_entropy(sample_graph, "Z")
        assert entropy == 0.0, f"Expected 0.0 for nonexistent node, got {entropy}"

class TestComputeFeaturesForNode:
    """Tests for compute_features_for_node function."""
    
    def test_full_feature_set(self, sample_graph):
        """Test that compute_features_for_node returns both metrics."""
        features = compute_features_for_node(sample_graph, "A")
        
        assert "bottleneck_resolution_ratio" in features
        assert "branching_entropy" in features
        assert features["bottleneck_resolution_ratio"] == 0.75
        assert math.isclose(features["branching_entropy"], 1.5, rel_tol=1e-9)
    
    def test_zero_outgoing_edges(self, sample_graph):
        """Test features for a node with no outgoing edges."""
        features = compute_features_for_node(sample_graph, "D")
        
        assert features["bottleneck_resolution_ratio"] == 0.0
        assert features["branching_entropy"] == 0.0

class TestComputeFeaturesDataFrame:
    """Tests for compute_features_dataframe function."""
    
    def test_dataframe_structure(self, sample_graph):
        """Test that the output DataFrame has the correct columns."""
        df = compute_features_dataframe(sample_graph)
        
        assert "node_id" in df.columns
        assert "bottleneck_resolution_ratio" in df.columns
        assert "branching_entropy" in df.columns
    
    def test_dataframe_row_count(self, sample_graph):
        """Test that the DataFrame has the correct number of rows."""
        df = compute_features_dataframe(sample_graph)
        assert len(df) == 5  # All 5 nodes should be processed
    
    def test_dataframe_specific_values(self, sample_graph):
        """Test specific values in the DataFrame."""
        df = compute_features_dataframe(sample_graph)
        
        # Find row for node A
        row_a = df[df["node_id"] == "A"].iloc[0]
        assert row_a["bottleneck_resolution_ratio"] == 0.75
        assert math.isclose(row_a["branching_entropy"], 1.5, rel_tol=1e-9)
        
        # Find row for node D
        row_d = df[df["node_id"] == "D"].iloc[0]
        assert row_d["bottleneck_resolution_ratio"] == 0.0
        assert row_d["branching_entropy"] == 0.0
    
    def test_subset_of_nodes(self, sample_graph):
        """Test computing features for a subset of nodes."""
        df = compute_features_dataframe(sample_graph, nodes=["A", "B"])
        
        assert len(df) == 2
        assert set(df["node_id"].tolist()) == {"A", "B"}

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
