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
    G.add_node("1", primary_cluster=0, bridging_coefficient=0.5)
    G.add_node("2", primary_cluster=0, bridging_coefficient=0.2)
    G.add_node("3", primary_cluster=1, bridging_coefficient=0.8)
    G.add_edge("1", "2")
    G.add_edge("2", "3")
    return G

@pytest.fixture
def invalid_graph():
    G = nx.Graph()
    G.add_node("1", primary_cluster=None, bridging_coefficient=0.5)
    G.add_node("2", primary_cluster=0, bridging_coefficient=1.5) # Invalid > 1.0
    return G

@pytest.fixture
def empty_graph():
    return nx.Graph()

def test_validate_sampled_graph_basic(valid_graph):
    validation, topology = validate_sampled_graph(valid_graph)
    assert validation["sampled_node_count"] == 3
    assert validation["valid_bridging_count"] == 3
    assert validation["valid_cluster_count"] == 3
    assert validation["representativeness_passed"] is True
    assert topology["checks_passed"] is True

def test_validate_sampled_graph_invalid_fields(invalid_graph):
    validation, topology = validate_sampled_graph(invalid_graph)
    assert validation["sampled_node_count"] == 2
    assert validation["valid_bridging_count"] == 1 # Only node 1 is valid
    assert validation["valid_cluster_count"] == 1 # Only node 2 is valid
    assert validation["representativeness_passed"] is False
    assert len(validation["errors"]) > 0

def test_validate_sampled_graph_empty_graph(empty_graph):
    validation, topology = validate_sampled_graph(empty_graph)
    assert validation["sampled_node_count"] == 0
    assert validation["representativeness_passed"] is False

def test_validate_sampled_graph_output_format(valid_graph):
    validation, topology = validate_sampled_graph(valid_graph)
    
    # Check required keys in validation
    assert "sampled_node_count" in validation
    assert "valid_bridging_count" in validation
    assert "valid_cluster_count" in validation
    assert "representativeness_passed" in validation
    
    # Check required keys in topology
    assert "degree_distribution" in topology
    assert "cluster_size_distribution" in topology
    assert "checks_passed" in topology

def test_validate_sampled_graph_file_write(valid_graph):
    with tempfile.TemporaryDirectory() as tmpdir:
        # We simulate the main function logic here
        validation, topology = validate_sampled_graph(valid_graph)
        
        path1 = os.path.join(tmpdir, "sampling_validation.json")
        path2 = os.path.join(tmpdir, "topology_equivalence.json")
        
        with open(path1, "w") as f:
            json.dump(validation, f)
        with open(path2, "w") as f:
            json.dump(topology, f)
        
        assert os.path.exists(path1)
        assert os.path.exists(path2)
        
        with open(path1) as f:
            data = json.load(f)
            assert data["sampled_node_count"] == 3
