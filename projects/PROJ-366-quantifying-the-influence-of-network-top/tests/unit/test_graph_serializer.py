"""
Unit tests for graph serialization logic.
"""
import os
import json
import pickle
import tempfile
import hashlib
from pathlib import Path
import pytest

from ingest.graph_serializer import calculate_checksum, serialize_graph, save_checksum_manifest

def test_calculate_checksum():
    """Test that checksum calculation is deterministic and correct."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = b"test data for checksum"
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        checksum = calculate_checksum(tmp_path)
        expected = hashlib.sha256(content).hexdigest()
        assert checksum == expected, f"Checksum mismatch: {checksum} != {expected}"
    finally:
        tmp_path.unlink()

def test_serialize_graph():
    """Test that graph serialization creates a valid pickle file."""
    mock_graph = {
        "node_count": 100,
        "edge_count": 250,
        "positions": [[0.0, 0.0, 0.0]],
        "metadata": {"source": "test"}
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_graph.pkl"
        
        checksum = serialize_graph(mock_graph, output_path)
        
        assert output_path.exists(), "Output file was not created."
        assert len(checksum) == 64, "Checksum should be 64 hex chars."

        # Verify content can be loaded
        with open(output_path, 'rb') as f:
            loaded_graph = pickle.load(f)
        
        assert loaded_graph["node_count"] == mock_graph["node_count"]
        assert loaded_graph["edge_count"] == mock_graph["edge_count"]

def test_save_checksum_manifest():
    """Test manifest saving and loading."""
    manifest_data = [
        {"file": "a.pkl", "checksum": "abc123"},
        {"file": "b.pkl", "checksum": "def456"}
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "manifest.json"
        
        save_checksum_manifest(manifest_data, manifest_path)
        
        assert manifest_path.exists()
        
        with open(manifest_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == manifest_data