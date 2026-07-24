import pytest
import json
import networkx as nx
from pathlib import Path
import tempfile
import shutil

from code.graph_builder import (
    parse_trajectory,
    detect_citations,
    build_co_reference_graph,
    build_dag,
    save_graph,
    get_nlp
)
from code.config import cutoff_depth

@pytest.fixture
def sample_trajectory():
    return {
        "id": "test_traj_001",
        "spans": [
            {"text": "This is the first span [1].", "role": "thought"},
            {"text": "Based on [1], the second span.", "role": "action"},
            {"text": "A third span with no citations.", "role": "observation"},
            {"text": "Referencing [1] again.", "role": "thought"}
        ]
    }

@pytest.fixture
def short_trajectory():
    return {
        "id": "short_traj",
        "spans": [
            {"text": "Only one span here.", "role": "thought"}
        ]
    }

@pytest.fixture
def empty_trajectory():
    return {
        "id": "empty_traj",
        "spans": []
    }

def test_parse_trajectory_full(sample_trajectory):
    # cutoff_depth is 1.0 in config usually, but let's test logic
    # Assuming config.cutoff_depth is 0.5 for testing partial, or 1.0 for full
    # We'll test with a specific fraction
    result = parse_trajectory(sample_trajectory, 0.5)
    # 4 spans * 0.5 = 2 spans
    assert len(result) == 2

def test_parse_trajectory_full_all(sample_trajectory):
    result = parse_trajectory(sample_trajectory, 1.0)
    assert len(result) == 4

def test_parse_trajectory_short_trajectory(short_trajectory):
    # Even if cutoff implies 0, we should get at least 1 if spans exist and depth > 0
    result = parse_trajectory(short_trajectory, 0.5)
    assert len(result) == 1

def test_parse_trajectory_empty(empty_trajectory):
    result = parse_trajectory(empty_trajectory, 0.5)
    assert len(result) == 0

def test_detect_citations():
    nlp = get_nlp()
    text = "Here is a citation [1] and another [2] and (Smith, 2020)."
    cites = detect_citations(text, nlp)
    assert "[1]" in cites
    assert "[2]" in cites
    assert "(Smith, 2020)" in cites

def test_build_co_reference_graph(sample_trajectory):
    spans = sample_trajectory["spans"]
    nlp = get_nlp()
    G = build_co_reference_graph(spans, nlp)
    
    assert G.number_of_nodes() == 4
    # Node 0 and 1 share [1], Node 0 and 3 share [1], Node 1 and 3 share [1]
    # Edges should be directed from lower index to higher
    assert G.has_edge(0, 1)
    assert G.has_edge(0, 3)
    assert G.has_edge(1, 3)
    # Node 2 has no citations, so no edges involving 2 based on citations
    assert not G.has_edge(0, 2)
    assert not G.has_edge(1, 2)
    assert not G.has_edge(2, 3)

def test_build_dag(sample_trajectory):
    G = build_dag(sample_trajectory, 1.0)
    assert G.number_of_nodes() == 4
    assert G.number_of_edges() > 0

def test_build_dag_short_trajectory(short_trajectory):
    G = build_dag(short_trajectory, 1.0)
    assert G.number_of_nodes() == 1
    assert G.number_of_edges() == 0

def test_build_dag_empty(empty_trajectory):
    G = build_dag(empty_trajectory, 1.0)
    assert G.number_of_nodes() == 0
    assert G.number_of_edges() == 0

def test_save_graph(tmp_path):
    G = nx.DiGraph()
    G.add_node(0, text="test", citations=["[1]"])
    G.add_node(1, text="test2", citations=["[1]"])
    G.add_edge(0, 1, type="citation_overlap")
    
    output_dir = tmp_path / "graphs"
    path = save_graph(G, "test_id_123", output_dir)
    
    assert path.exists()
    assert path.suffix == ".json"
    
    with open(path, "r") as f:
        data = json.load(f)
    
    assert data["trajectory_id"] == "test_id_123"
    assert data["num_nodes"] == 2
    assert data["num_edges"] == 1
    assert data["nodes"][0]["id"] == 0
    assert "[1]" in data["nodes"][0]["citations"]

def test_short_trajectory_handling():
    """
    Test T016a: Handle trajectories shorter than cutoff.
    If spans are few, we should use all of them.
    """
    traj = {
        "id": "tiny",
        "spans": [{"text": "a"}, {"text": "b"}]
    }
    # cutoff 0.5 -> 1 span, cutoff 0.1 -> 0 spans (should force 1)
    G = build_dag(traj, 0.1)
    # Should have at least 1 node if spans exist
    assert G.number_of_nodes() >= 1

def test_zero_edge_graph():
    """
    Test T016b: Handle zero-edge cases.
    """
    traj = {
        "id": "no_cites",
        "spans": [
            {"text": "No cites here"},
            {"text": "Also no cites"}
        ]
    }
    G = build_dag(traj, 1.0)
    assert G.number_of_nodes() == 2
    assert G.number_of_edges() == 0
    # Connectivity should be 0.0
    # (Handled in metrics, but graph structure is correct here)
    assert nx.is_connected(G.to_undirected()) == False or G.number_of_nodes() <= 1
    if G.number_of_nodes() > 1:
        assert nx.number_connected_components(G.to_undirected()) == 2
