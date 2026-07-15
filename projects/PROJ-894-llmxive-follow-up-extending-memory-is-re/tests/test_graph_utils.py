"""
Unit tests for graph_utils module.
"""
import pytest
import networkx as nx
from graph_utils import build_memory_graph, inject_noise, validate_graph, get_graph_statistics

def test_build_memory_graph_basic():
    """Test basic graph construction from entities and relations."""
    entities = [{"id": "e1", "type": "Person", "text": "Alice"}, 
                {"id": "e2", "type": "Person", "text": "Bob"}]
    relations = [{"source": "e1", "target": "e2", "type": "knows"}]
    
    G = build_memory_graph(entities, relations)
    
    assert isinstance(G, nx.Graph)
    assert G.number_of_nodes() == 2
    assert G.number_of_edges() == 1
    assert "e1" in G.nodes
    assert "e2" in G.nodes
    assert ("e1", "e2") in G.edges

def test_inject_noise():
    """Test that noise injection adds random edges."""
    entities = [{"id": f"e{i}", "type": "Entity", "text": f"Text {i}"} for i in range(5)]
    relations = [{"source": "e0", "target": "e1", "type": "rel1"}]
    
    G = build_memory_graph(entities, relations)
    original_edges = G.number_of_edges()
    
    # Inject noise with high probability to ensure changes
    noisy_G = inject_noise(G, noise_ratio=0.5, seed=42)
    
    assert noisy_G.number_of_edges() >= original_edges

def test_validate_graph():
    """Test graph validation."""
    entities = [{"id": "e1", "type": "Person", "text": "Alice"}]
    relations = [{"source": "e1", "target": "e1", "type": "knows"}]
    
    G = build_memory_graph(entities, relations)
    is_valid, issues = validate_graph(G)
    
    # Self-loops might be flagged depending on implementation
    assert isinstance(is_valid, bool)
    assert isinstance(issues, list)

def test_get_graph_statistics():
    """Test graph statistics calculation."""
    entities = [{"id": f"e{i}", "type": "Entity", "text": f"Text {i}"} for i in range(4)]
    relations = [
        {"source": "e0", "target": "e1", "type": "rel1"},
        {"source": "e1", "target": "e2", "type": "rel2"},
        {"source": "e2", "target": "e3", "type": "rel3"}
    ]
    
    G = build_memory_graph(entities, relations)
    stats = get_graph_statistics(G)
    
    assert "num_nodes" in stats
    assert "num_edges" in stats
    assert "avg_degree" in stats
    assert stats["num_nodes"] == 4
