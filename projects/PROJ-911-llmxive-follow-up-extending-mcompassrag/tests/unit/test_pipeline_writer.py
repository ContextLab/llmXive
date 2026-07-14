"""
Unit tests for T016: pipeline_writer.py

Tests verify that the writer correctly handles data loading and file writing.
"""
import json
import csv
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to mock the config paths to use a temp directory for testing
import sys
from io import StringIO

# Mock config to point to a temp directory
class MockConfig:
    PROCESSED_DIR = Path(tempfile.mkdtemp())
    RANDOM_SEED = 42

# Patch the config module before importing the writer
sys.modules['code.config'] = MockConfig()

# Now import the functions we want to test (we need to re-define them locally 
# or import from the module if we can patch the imports inside the module)
# Since the module imports from code.config, we must patch the module itself
# to use our mock config.

# Instead, let's test the logic by mocking the file I/O and dependencies.

def test_write_final_graphs_json():
    """Test that graphs are written to JSON correctly."""
    from code.pipeline_writer import write_final_graphs_json
    
    test_graphs = [
        {"doc_id": "doc1", "nodes": ["a", "b"], "edges": [["a", "b"]]},
        {"doc_id": "doc2", "nodes": ["x", "y"], "edges": [["x", "y"]]}
    ]
    
    # The function writes to PROCESSED_DIR / 'graphs.json'
    # We need to ensure the directory exists
    MockConfig.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = write_final_graphs_json(test_graphs)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    
    assert len(loaded) == 2
    assert loaded[0]["doc_id"] == "doc1"
    assert loaded[1]["doc_id"] == "doc2"

def test_write_final_features_csv():
    """Test that features are written to CSV correctly."""
    from code.pipeline_writer import write_final_features_csv
    
    test_features = [
        {"doc_id": "doc1", "modularity": 0.5, "avg_path": 2.0},
        {"doc_id": "doc2", "modularity": 0.3, "avg_path": 3.5}
    ]
    
    MockConfig.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = write_final_features_csv(test_features)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]["doc_id"] == "doc1"
    assert float(rows[0]["modularity"]) == 0.5
    assert float(rows[1]["avg_path"]) == 3.5

def test_write_final_features_csv_empty():
    """Test handling of empty features list."""
    from code.pipeline_writer import write_final_features_csv
    
    MockConfig.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # This should not raise an error, though it might log a warning
    output_path = write_final_features_csv([])
    assert output_path.exists()