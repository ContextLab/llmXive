import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json
import logging

from src.data.graph_construction import (
    calculate_coordination_number,
    build_adjacency_matrix,
    extract_edge_attributes,
    construct_transition_state_graph,
    filter_outliers,
    run_graph_construction
)

# Setup logging for tests
logging.basicConfig(level=logging.INFO)

@pytest.fixture
def sample_distances():
    # 4x4 distance matrix (4 atoms)
    # Atom 0 at (0,0,0), Atom 1 at (1,0,0), Atom 2 at (2,0,0), Atom 3 at (0,3,0)
    # Distances:
    # 0-1: 1.0
    # 0-2: 2.0
    # 0-3: 3.0
    # 1-2: 1.0
    # 1-3: ~3.16
    # 2-3: ~3.60
    dists = np.array([
        [0.0, 1.0, 2.0, 3.0],
        [1.0, 0.0, 1.0, 3.162],
        [2.0, 1.0, 0.0, 3.605],
        [3.0, 3.162, 3.605, 0.0]
    ])
    return dists

@pytest.fixture
def sample_atomic_numbers():
    return np.array([6, 1, 1, 8])  # C, H, H, O

@pytest.fixture
def sample_formal_charges():
    return np.array([0, 0, 0, 0])

def test_calculate_coordination_number(sample_distances):
    # Cutoff 1.5: Atom 0 has 1 neighbor (Atom 1)
    cn = calculate_coordination_number(sample_distances[0], 1.5)
    assert cn == 1

    # Cutoff 2.5: Atom 0 has 2 neighbors (Atom 1, Atom 2)
    cn = calculate_coordination_number(sample_distances[0], 2.5)
    assert cn == 2

    # Cutoff 0.5: No neighbors
    cn = calculate_coordination_number(sample_distances[0], 0.5)
    assert cn == 0

def test_build_adjacency_matrix(sample_distances):
    adj = build_adjacency_matrix(sample_distances, 1.5)
    # Should have edges 0-1 and 1-2
    assert adj[0, 1] == 1
    assert adj[1, 0] == 1
    assert adj[1, 2] == 1
    assert adj[2, 1] == 1
    assert adj[0, 2] == 0
    assert adj[0, 0] == 0

def test_extract_edge_attributes(sample_distances):
    edge_idx, edge_dists, edge_types = extract_edge_attributes(sample_distances, 1.5)
    
    # Check number of edges (undirected, so 2 per connection)
    # Connections: 0-1, 1-2. Total 4 directed edges.
    assert len(edge_idx) == 4
    assert len(edge_dists) == 4
    
    # Check values
    # 0-1 and 1-0
    assert 1.0 in edge_dists
    assert 1.0 in edge_dists

def test_construct_transition_state_graph(sample_atomic_numbers, sample_formal_charges, sample_distances):
    graph = construct_transition_state_graph(
        atomic_numbers=sample_atomic_numbers,
        formal_charges=sample_formal_charges,
        distances=sample_distances,
        cutoff=1.5
    )
    
    assert len(graph["nodes"]) == 4
    assert graph["metadata"]["num_nodes"] == 4
    assert "edge_index" in graph["edges"]
    assert "edge_distance" in graph["edges"]
    assert "coordination_numbers" in graph["metadata"]

def test_filter_outliers(sample_atomic_numbers, sample_formal_charges, sample_distances):
    # Create a graph with high coordination
    # Modify distances to create many neighbors
    high_cn_dists = np.ones((4, 4)) * 0.5
    np.fill_diagonal(high_cn_dists, 0.0)
    
    graph = construct_transition_state_graph(
        atomic_numbers=sample_atomic_numbers,
        formal_charges=sample_formal_charges,
        distances=high_cn_dists,
        cutoff=1.5
    )
    graph["metadata"]["graph_id"] = 0
    
    graphs = [graph]
    all_graphs, flagged = filter_outliers(graphs, max_coord=2)
    
    assert len(all_graphs) == 1
    assert len(flagged) == 1

def test_run_graph_construction_integration(sample_atomic_numbers, sample_formal_charges, sample_distances):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create input data
        input_df = pd.DataFrame({
            "atomic_numbers": [sample_atomic_numbers.tolist()],
            "formal_charges": [sample_formal_charges.tolist()],
            "distances": [sample_distances.tolist()]
        })
        
        input_path = tmpdir / "input.parquet"
        output_path = tmpdir / "output.parquet"
        
        input_df.to_parquet(input_path)
        
        run_graph_construction(input_path, output_path, cutoff=1.5)
        
        assert output_path.exists()
        
        # Load and verify
        result_df = pd.read_parquet(output_path)
        assert len(result_df) == 1
        
        # Verify metadata
        meta = json.loads(result_df["metadata"].iloc[0])
        assert meta["num_nodes"] == 4
        assert meta["cutoff_used"] == 1.5