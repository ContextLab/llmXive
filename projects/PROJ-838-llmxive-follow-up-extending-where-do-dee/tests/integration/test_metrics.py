import os
import json
import csv
import tempfile
import shutil
import pytest
from pathlib import Path
import networkx as nx

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from metrics import process_batch, load_graph_from_json, calculate_global_connectivity, calculate_average_branching_factor

@pytest.fixture
def temp_graph_dir():
    """Create a temporary directory with sample graph JSON files."""
    temp_dir = tempfile.mkdtemp()
    
    # Create sample graph 1: 3 nodes, 2 edges
    G1 = nx.DiGraph()
    G1.add_nodes_from(['A', 'B', 'C'])
    G1.add_edges_from([('A', 'B'), ('B', 'C')])
    data1 = {'nodes': list(G1.nodes()), 'edges': list(G1.edges())}
    with open(os.path.join(temp_dir, 'trajectory_001.json'), 'w') as f:
        json.dump(data1, f)
    
    # Create sample graph 2: 2 nodes, 1 edge
    G2 = nx.DiGraph()
    G2.add_nodes_from(['X', 'Y'])
    G2.add_edges_from([('X', 'Y')])
    data2 = {'nodes': list(G2.nodes()), 'edges': list(G2.edges())}
    with open(os.path.join(temp_dir, 'trajectory_002.json'), 'w') as f:
        json.dump(data2, f)
    
    # Create sample graph 3: 1 node, 0 edges (edge case)
    G3 = nx.DiGraph()
    G3.add_node('Z')
    data3 = {'nodes': list(G3.nodes()), 'edges': []}
    with open(os.path.join(temp_dir, 'trajectory_003.json'), 'w') as f:
        json.dump(data3, f)

    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_output_csv():
    """Create a temporary path for output CSV."""
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, 'metrics.csv')
    yield output_path
    shutil.rmtree(temp_dir)

def test_process_batch_writes_csv(temp_graph_dir, temp_output_csv):
    """
    Integration test for T023: Verify process_batch writes a valid CSV 
    with the correct schema and row count matching input graph files.
    """
    # Run the batch processing
    process_batch(temp_graph_dir, temp_output_csv)
    
    # Verify the file exists
    assert os.path.exists(temp_output_csv), "Output CSV file was not created."
    
    # Read and validate the CSV content
    with open(temp_output_csv, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Check row count matches input files (3 graphs)
    assert len(rows) == 3, f"Expected 3 rows, got {len(rows)}"
    
    # Check headers
    expected_headers = ['trajectory_id', 'global_connectivity', 'avg_branching_factor']
    assert reader.fieldnames == expected_headers, f"Headers mismatch: {reader.fieldnames}"
    
    # Validate specific values for known graphs
    # trajectory_001: 3 nodes, 2 edges -> Connectivity = 2/(3*2) = 0.333..., Branching = 2/3 = 0.666...
    row1 = next(r for r in rows if r['trajectory_id'] == 'trajectory_001')
    assert abs(float(row1['global_connectivity']) - (2/6)) < 1e-6
    assert abs(float(row1['avg_branching_factor']) - (2/3)) < 1e-6
    
    # trajectory_003: 1 node, 0 edges -> Connectivity = 0.0, Branching = 0.0
    row3 = next(r for r in rows if r['trajectory_id'] == 'trajectory_003')
    assert float(row3['global_connectivity']) == 0.0
    assert float(row3['avg_branching_factor']) == 0.0

def test_process_batch_handles_malformed_json(temp_output_csv):
    """
    Test that process_batch logs errors for malformed JSON but continues processing.
    """
    temp_dir = tempfile.mkdtemp()
    
    # Create a valid graph
    G_valid = nx.DiGraph()
    G_valid.add_nodes_from(['A', 'B'])
    G_valid.add_edges_from([('A', 'B')])
    data_valid = {'nodes': list(G_valid.nodes()), 'edges': list(G_valid.edges())}
    with open(os.path.join(temp_dir, 'valid_trajectory.json'), 'w') as f:
        json.dump(data_valid, f)
    
    # Create a malformed JSON file
    with open(os.path.join(temp_dir, 'malformed_trajectory.json'), 'w') as f:
        f.write("{ invalid json }")
    
    try:
        process_batch(temp_dir, temp_output_csv)
        
        # Should have written at least one row for the valid file
        assert os.path.exists(temp_output_csv)
        with open(temp_output_csv, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1, "Should have processed the valid file despite the malformed one."
    finally:
        shutil.rmtree(temp_dir)
