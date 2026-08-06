import os
import json
import csv
import pytest
from pathlib import Path
import networkx as nx

# Ensure we can import the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from metrics import process_batch, calculate_global_connectivity, calculate_average_branching_factor

@pytest.fixture
def temp_graph_dir(tmp_path):
    """Create a temporary directory with sample graph JSON files."""
    graph_dir = tmp_path / "graphs"
    graph_dir.mkdir()

    # Create a valid graph with 3 nodes and 2 edges
    G1 = nx.DiGraph()
    G1.add_nodes_from([1, 2, 3])
    G1.add_edges_from([(1, 2), (2, 3)])
    
    with open(graph_dir / "trajectory_001.json", 'w') as f:
        json.dump({
            "nodes": list(G1.nodes()),
            "edges": list(G1.edges())
        }, f)

    # Create another valid graph
    G2 = nx.DiGraph()
    G2.add_nodes_from([10, 20])
    G2.add_edges_from([(10, 20)])
    
    with open(graph_dir / "trajectory_002.json", 'w') as f:
        json.dump({
            "nodes": list(G2.nodes()),
            "edges": list(G2.edges())
        }, f)

    # Create an empty graph (0 edges)
    G3 = nx.DiGraph()
    G3.add_nodes_from([5, 6, 7])
    
    with open(graph_dir / "trajectory_003.json", 'w') as f:
        json.dump({
            "nodes": list(G3.nodes()),
            "edges": list(G3.edges())
        }, f)

    return str(graph_dir)

@pytest.fixture
def temp_output_path(tmp_path):
    """Create a temporary path for the output CSV."""
    return str(tmp_path / "metrics.csv")

def test_process_batch_writes_csv(temp_graph_dir, temp_output_path):
    """
    Integration test for T023: Verify process_batch writes a valid CSV 
    with the correct schema and row count.
    """
    # Execute the batch processing
    process_batch(temp_graph_dir, temp_output_path)

    # Verify the file exists
    output_file = Path(temp_output_path)
    assert output_file.exists(), "Output CSV file was not created."

    # Verify the CSV content
    with open(output_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Check row count matches input graph count
    assert len(rows) == 3, f"Expected 3 rows, found {len(rows)}"

    # Check schema
    expected_headers = ['trajectory_id', 'global_connectivity', 'avg_branching_factor']
    assert reader.fieldnames == expected_headers, f"Headers mismatch: {reader.fieldnames}"

    # Verify specific values for trajectory_001 (3 nodes, 2 edges)
    # Connectivity = 2 / (3*2) = 2/6 = 0.333...
    # Branching = (1+1+0) / 3 = 0.666...
    row1 = next(r for r in rows if r['trajectory_id'] == 'trajectory_001')
    assert float(row1['global_connectivity']) == pytest.approx(0.333333, rel=0.01)
    assert float(row1['avg_branching_factor']) == pytest.approx(0.666666, rel=0.01)

    # Verify trajectory_003 (3 nodes, 0 edges) -> Connectivity 0.0
    row3 = next(r for r in rows if r['trajectory_id'] == 'trajectory_003')
    assert float(row3['global_connectivity']) == 0.0
    assert float(row3['avg_branching_factor']) == 0.0

def test_process_batch_handles_malformed_json(temp_path):
    """
    Test that process_batch logs an error and continues when encountering malformed JSON.
    """
    graph_dir = temp_path / "graphs"
    graph_dir.mkdir()
    output_path = str(temp_path / "metrics.csv")

    # Create a valid graph
    G_valid = nx.DiGraph()
    G_valid.add_nodes_from([1, 2])
    G_valid.add_edges_from([(1, 2)])
    with open(graph_dir / "valid.json", 'w') as f:
        json.dump({"nodes": [1, 2], "edges": [(1, 2)]}, f)

    # Create a malformed JSON file
    with open(graph_dir / "malformed.json", 'w') as f:
        f.write("{ this is not valid json }")

    # Run process_batch - it should not crash
    process_batch(str(graph_dir), output_path)

    # Verify the valid file was processed
    with open(output_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]['trajectory_id'] == 'valid'
