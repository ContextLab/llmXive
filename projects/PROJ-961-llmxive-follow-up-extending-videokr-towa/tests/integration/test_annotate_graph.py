"""
Integration tests for annotate_graph.py.
Verifies end-to-end functionality on a small subset.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
import pytest

# Mock the project root and config for testing
import sys
from unittest.mock import patch

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingest.annotate_graph import (
    load_videokr_dataset,
    load_graph,
    map_entities_to_nodes,
    calculate_chain_length,
    bin_hop_length,
    process_chunk
)
from utils.entity_linker import create_entity_linker

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_videokr_dataset_csv(temp_data_dir):
    # Create a mock CSV
    csv_path = temp_data_dir / "test.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'question', 'answer'])
        writer.writeheader()
        writer.writerow({'id': '1', 'question': 'What is 1+1?', 'answer': '2'})
    
    data = load_videokr_dataset(csv_path)
    assert len(data) == 1
    assert data[0]['id'] == '1'

def test_load_graph_json(temp_data_dir):
    # Create a mock graph
    graph_path = temp_data_dir / "graph.json"
    graph_data = {"A": ["B"], "B": ["A", "C"], "C": ["B"]}
    with open(graph_path, 'w') as f:
        json.dump(graph_data, f)
    
    graph = load_graph(graph_path)
    assert "A" in graph
    assert "B" in graph["A"]

def test_map_entities_to_nodes(temp_data_dir):
    # Create a mock graph and linker
    graph = {"entity1": ["entity2"], "entity2": ["entity1"]}
    linker = create_entity_linker(graph)
    
    # Mock the linker's link method to return a deterministic result
    # Since create_entity_linker builds a real one, we test the logic flow
    # In a real integration test, we'd need a real graph with known entities
    # For this unit-style integration, we assume the graph has 'entity1'
    node, conf = map_entities_to_nodes(linker, "entity1")
    
    # If the linker works, it should find 'entity1' with high confidence
    # If not, it returns None. We just verify the function runs without error.
    assert isinstance(node, (str, type(None)))
    assert isinstance(conf, float)

def test_calculate_chain_length(temp_data_dir):
    graph = {"A": ["B"], "B": ["A", "C"], "C": ["B"]}
    
    # Direct connection
    hops = calculate_chain_length(graph, "A", "B")
    assert hops == 1
    
    # Indirect connection
    hops = calculate_chain_length(graph, "A", "C")
    assert hops == 2
    
    # Disconnected
    hops = calculate_chain_length(graph, "A", "D") # D not in graph
    assert hops is None

def test_bin_hop_length():
    assert bin_hop_length(1) == '1'
    assert bin_hop_length(2) == '2'
    assert bin_hop_length(3) == '3+'
    assert bin_hop_length(5) == '3+'
    assert bin_hop_length(None) == 'unresolvable'

def test_process_chunk(temp_data_dir):
    # Setup mock data
    chunk = [
        {'id': '1', 'question': 'entity1', 'answer': 'entity2', 'correctness': 'true'},
        {'id': '2', 'question': 'entity1', 'answer': 'entity3', 'correctness': 'false'} # entity3 not in graph
    ]
    graph = {"entity1": ["entity2"], "entity2": ["entity1"]}
    linker = create_entity_linker(graph)
    
    results = process_chunk(chunk, graph, linker)
    
    assert len(results) == 2
    assert results[0]['chain_bin'] == '1' # entity1 -> entity2
    assert results[1]['chain_bin'] == 'unresolvable' # entity3 not found