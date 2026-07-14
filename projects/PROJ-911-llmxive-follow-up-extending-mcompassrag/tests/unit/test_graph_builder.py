"""
Unit test for graph edge case: low term diversity (< 5 unique terms).
"""
import pytest
import networkx as nx
from pathlib import Path
import sys
import json

if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.graph_builder import build_co_occurrence_graph, tokenize_and_filter
from code.config import PROCESSED_DIR


@pytest.fixture
def sample_vocab():
    """Create a minimal vocabulary for testing."""
    return {"the", "data", "graph", "node", "edge", "test", "low", "diversity"}


def test_low_term_diversity_empty_graph(sample_vocab):
    """
    Test that a document with 0 unique terms after filtering results in an empty graph
    without raising an exception.
    """
    text = "xxxxx yyyyy zzzzz"  # Tokens not in vocab
    tokens = tokenize_and_filter(text, sample_vocab)
    
    assert len(tokens) == 0, "Expected no tokens after filtering"
    
    G = build_co_occurrence_graph(tokens, window_size=10)
    
    assert G.number_of_nodes() == 0
    assert G.number_of_edges() == 0
    assert isinstance(G, nx.Graph)


def test_low_term_diversity_single_node(sample_vocab):
    """
    Test that a document with only 1 unique term results in a graph with 1 node and 0 edges.
    """
    text = "data data data"
    tokens = tokenize_and_filter(text, sample_vocab)
    
    assert len(tokens) == 3
    assert len(set(tokens)) == 1
    
    G = build_co_occurrence_graph(tokens, window_size=10)
    
    assert G.number_of_nodes() == 1
    assert G.number_of_edges() == 0
    assert list(G.nodes()) == ["data"]


def test_low_term_diversity_threshold_boundary(sample_vocab):
    """
    Test the boundary case where unique terms are exactly 4 (below threshold of 5).
    The graph should still be built, but the topology extractor might flag it.
    This test ensures the graph builder itself doesn't crash.
    """
    # Use terms present in vocab
    text = "data graph node edge data graph"
    tokens = tokenize_and_filter(text, sample_vocab)
    
    unique_terms = set(tokens)
    assert len(unique_terms) == 4  # data, graph, node, edge
    
    G = build_co_occurrence_graph(tokens, window_size=10)
    
    # Should have 4 nodes
    assert G.number_of_nodes() == 4
    # Should have edges because terms co-occur in the window
    assert G.number_of_edges() > 0


def test_normal_diversity_graph(sample_vocab):
    """
    Test that a document with >= 5 unique terms builds a normal graph.
    """
    text = "data graph node edge test low diversity the"
    tokens = tokenize_and_filter(text, sample_vocab)
    
    unique_terms = set(tokens)
    assert len(unique_terms) >= 5
    
    G = build_co_occurrence_graph(tokens, window_size=10)
    
    assert G.number_of_nodes() == len(unique_terms)
    assert G.number_of_edges() > 0
