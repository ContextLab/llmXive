import json
import os
import tempfile
from pathlib import Path

import networkx as nx
import pytest

from graph_builder import build_dag, save_graph, parse_trajectory, build_co_reference_graph
from config import ensure_directories

@pytest.fixture
def sample_trajectory():
    """
    Create a sample trajectory with spans that have citations.
    """
    return {
        "id": "sample_001",
        "spans": [
            {"id": 0, "text": "Initial thought [1]."},
            {"id": 1, "text": "Based on [1], I proceed."},
            {"id": 2, "text": "Another reference [2]."},
            {"id": 3, "text": "Combining [1] and [2]."},
            {"id": 4, "text": "Final conclusion."}
        ]
    }

@pytest.fixture
def empty_trajectory():
    return {"id": "empty_001", "spans": []}

@pytest.fixture
def short_trajectory():
    return {"id": "short_001", "spans": [{"id": 0, "text": "Only one span."}]}

def test_parse_trajectory_cutoff(sample_trajectory):
    # With 5 spans and cutoff 0.5, we expect 2 spans
    spans = parse_trajectory(sample_trajectory, cutoff_depth=0.5)
    assert len(spans) == 2
    assert spans[0]["id"] == 0
    assert spans[1]["id"] == 1

def test_parse_trajectory_full(sample_trajectory):
    # With cutoff 1.0, we expect all spans
    spans = parse_trajectory(sample_trajectory, cutoff_depth=1.0)
    assert len(spans) == 5

def test_parse_trajectory_zero_cutoff(empty_trajectory):
    spans = parse_trajectory(empty_trajectory, cutoff_depth=0.5)
    assert len(spans) == 0

def test_build_dag_citation_edges(sample_trajectory):
    """
    Test that the DAG correctly identifies citation-based edges.
    Span 0 has [1], Span 1 has [1], Span 3 has [1].
    Edges should be: 0->1, 0->3, 1->3.
    """
    dag = build_dag(sample_trajectory, cutoff_depth=1.0)
    
    # Check nodes
    assert len(dag.nodes()) == 5
    
    # Check edges
    # 0 -> 1 (shared [1])
    assert dag.has_edge(0, 1)
    # 0 -> 3 (shared [1])
    assert dag.has_edge(0, 3)
    # 1 -> 3 (shared [1])
    assert dag.has_edge(1, 3)
    # 2 -> 3 (shared [2])
    assert dag.has_edge(2, 3)
    
    # Check acyclic
    assert nx.is_directed_acyclic_graph(dag)

def test_build_dag_empty_trajectory(empty_trajectory):
    dag = build_dag(empty_trajectory, cutoff_depth=0.5)
    assert len(dag.nodes()) == 0
    assert len(dag.edges()) == 0

def test_save_graph(tmp_path):
    """
    Test that save_graph writes a valid JSON file.
    """
    # Create a simple graph
    G = nx.DiGraph()
    G.add_node(0, text="Node 0")
    G.add_node(1, text="Node 1")
    G.add_edge(0, 1, type="citation")
    
    output_dir = tmp_path / "graphs"
    file_path = save_graph(G, "test_traj", output_dir)
    
    assert os.path.exists(file_path)
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    assert data["edges"][0]["source"] == 0
    assert data["edges"][0]["target"] == 1

def test_save_graph_integration(tmp_path):
    """
    Integration test: Build a graph from a trajectory and save it.
    """
    trajectory = {
        "id": "int_test_01",
        "spans": [
            {"id": 0, "text": "Start [A]."},
            {"id": 1, "text": "Continue [A]."}
        ]
    }
    
    dag = build_dag(trajectory, cutoff_depth=1.0)
    output_dir = tmp_path / "processed" / "graphs"
    file_path = save_graph(dag, "int_test_01", output_dir)
    
    assert os.path.exists(file_path)
    
    # Verify content
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    assert data["nodes"][0]["id"] == 0
    assert data["nodes"][1]["id"] == 1
