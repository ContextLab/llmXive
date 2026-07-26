import os
import json
import csv
import pytest
from pathlib import Path
import networkx as nx

# Import the function under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from metrics import process_batch, load_graph_from_json

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
        nx.write_graphml(G1, f) # Using graphml for simplicity in test, but function expects JSON dict structure
    
    # Re-write as JSON dict to match load_graph_from_json expectation
    data1 = {'nodes': [1, 2, 3], 'edges': [[1, 2], [2, 3]]}
    with open(graph_dir / "trajectory_001.json", 'w') as f:
        json.dump(data1, f)

    # Create a second graph with 4 nodes and 3 edges
    data2 = {'nodes': [1, 2, 3, 4], 'edges': [[1, 2], [2, 3], [3, 4]]}
    with open(graph_dir / "trajectory_002.json", 'w') as f:
        json.dump(data2, f)
    
    # Create a graph with 0 edges (isolated nodes)
    data3 = {'nodes': [1, 2], 'edges': []}
    with open(graph_dir / "trajectory_003.json", 'w') as f:
        json.dump(data3, f)

    return graph_dir

def test_process_batch_writes_csv(temp_graph_dir, tmp_path):
    """
    Integration test for T023: Verify process_batch writes metrics.csv 
    with correct structure and row count.
    """
    output_file = tmp_path / "metrics.csv"
    
    # Execute the batch processing
    process_batch(str(temp_graph_dir), str(output_file))
    
    # Verification 1: File exists
    assert output_file.exists(), "metrics.csv was not created"
    
    # Verification 2: Row count matches input graph count (3 graphs)
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3, f"Expected 3 rows, found {len(rows)}"
    
    # Verification 3: Headers are correct
    expected_headers = ['trajectory_id', 'global_connectivity', 'avg_branching_factor']
    assert list(rows[0].keys()) == expected_headers, "CSV headers do not match expected"
    
    # Verification 4: Values are numeric and reasonable
    for row in rows:
        assert row['trajectory_id'].startswith('trajectory_'), "Invalid trajectory_id"
        assert float(row['global_connectivity']) >= 0.0, "Connectivity cannot be negative"
        assert float(row['avg_branching_factor']) >= 0.0, "Branching factor cannot be negative"
    
    # Verification 5: Specific check on zero-edge case (trajectory_003)
    zero_edge_row = next(r for r in rows if r['trajectory_id'] == 'trajectory_003')
    assert float(zero_edge_row['global_connectivity']) == 0.0, "Zero-edge graph should have 0.0 connectivity"
    assert float(zero_edge_row['avg_branching_factor']) == 0.0, "Zero-edge graph should have 0.0 branching"
    
    # Verification 6: Check connectivity calculation for trajectory_001 (3 nodes, 2 edges)
    # Connectivity = 2 / (3 * 2) = 2/6 = 0.333...
    row_001 = next(r for r in rows if r['trajectory_id'] == 'trajectory_001')
    expected_conn = 2 / 6
    assert abs(float(row_001['global_connectivity']) - expected_conn) < 1e-6, "Connectivity calculation incorrect"

def test_process_batch_handles_missing_dir(tmp_path):
    """Test that process_batch raises FileNotFoundError for missing directory."""
    with pytest.raises(FileNotFoundError):
        process_batch(str(tmp_path / "non_existent"), str(tmp_path / "out.csv"))

def test_process_batch_handles_empty_dir(tmp_path):
    """Test that process_batch raises ValueError for directory with no JSON files."""
    empty_dir = tmp_path / "empty_graphs"
    empty_dir.mkdir()
    
    with pytest.raises(ValueError):
        process_batch(str(empty_dir), str(tmp_path / "out.csv"))
