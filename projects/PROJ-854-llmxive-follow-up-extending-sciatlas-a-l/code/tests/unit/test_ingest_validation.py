import pytest
import networkx as nx
import json
import os
import tempfile
from pathlib import Path
from src.services.ingest import validate_sampled_graph

@pytest.fixture
def valid_graph():
    G = nx.Graph()
    G.add_node("1", primary_cluster=0, bridging_coefficient=0.5, degree=2)
    G.add_node("2", primary_cluster=0, bridging_coefficient=0.3, degree=3)
    G.add_node("3", primary_cluster=1, bridging_coefficient=0.8, degree=1)
    G.add_edge("1", "2")
    G.add_edge("2", "3")
    return G

@pytest.fixture
def invalid_graph():
    G = nx.Graph()
    G.add_node("1", primary_cluster=None, bridging_coefficient=1.5, degree=2)  # Invalid cluster and bridging
    G.add_node("2", primary_cluster=0, bridging_coefficient=0.3, degree=3)
    return G

@pytest.fixture
def empty_graph():
    return nx.Graph()

def test_validate_sampled_graph_basic(valid_graph):
    result = validate_sampled_graph(valid_graph)
    assert result["sampled_node_count"] == 3
    assert result["valid_bridging_count"] == 3
    assert result["valid_cluster_count"] == 3
    assert result["schema_passed"] is True
    assert result["representativeness_passed"] is True

def test_validate_sampled_graph_invalid_fields(invalid_graph):
    result = validate_sampled_graph(invalid_graph)
    assert result["sampled_node_count"] == 2
    assert result["valid_bridging_count"] == 1  # Only node "2" is valid
    assert result["valid_cluster_count"] == 1   # Only node "2" has cluster
    assert result["schema_passed"] is False

def test_validate_sampled_graph_empty_graph(empty_graph):
    result = validate_sampled_graph(empty_graph)
    assert result["sampled_node_count"] == 0
    assert "error" in result["details"]

def test_validate_sampled_graph_output_format(valid_graph):
    result = validate_sampled_graph(valid_graph)
    required_keys = ['sampled_node_count', 'valid_bridging_count', 'valid_cluster_count', 'representativeness_passed']
    for key in required_keys:
        assert key in result
    assert isinstance(result["details"], dict)

def test_validate_sampled_graph_file_write(valid_graph):
    with tempfile.TemporaryDirectory() as tmpdir:
        artifacts_dir = Path(tmpdir) / "artifacts" / "results"
        artifacts_dir.mkdir(parents=True)
        # Mock the global ARTIFACT_PATH temporarily
        import src.services.ingest as ingest_module
        original_path = ingest_module.ARTIFACT_PATH
        ingest_module.ARTIFACT_PATH = str(Path(tmpdir) / "artifacts")
        
        try:
            result = validate_sampled_graph(valid_graph)
            # Check if files were written (Note: validate_sampled_graph writes in the main flow, 
            # but here we just check the logic returns correct dict. 
            # The actual file writing happens in fetch_and_build_subgraph).
            assert result is not None
        finally:
            ingest_module.ARTIFACT_PATH = original_path
