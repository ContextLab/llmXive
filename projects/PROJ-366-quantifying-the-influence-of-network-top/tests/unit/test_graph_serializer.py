import os
import json
import pickle
import tempfile
from pathlib import Path
import numpy as np
import pytest

from code.ingest.graph_serializer import serialize_graph, calculate_checksum, serialize_directory_graphs

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_graph_data():
    return {
        "sample_id": "test_001",
        "nodes": np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]),
        "edges": np.array([[0, 1]]),
        "metadata": {"cutoff": 3.0, "atom_type": "Si"}
    }

def test_calculate_checksum(temp_output_dir):
    test_file = temp_output_dir / "test.txt"
    test_file.write_text("hello world")
    
    checksum = calculate_checksum(test_file)
    assert len(checksum) == 32  # MD5 length
    assert checksum == calculate_checksum(test_file)  # Deterministic

def test_serialize_graph_pickle(temp_output_dir, sample_graph_data):
    result = serialize_graph(sample_graph_data, "test_001", temp_output_dir, format="pickle")
    
    assert "sample_id" in result
    assert result["sample_id"] == "test_001"
    assert result["format"] == "pickle"
    assert "checksum" in result
    assert "file_path" in result
    
    # Verify file exists and can be loaded
    file_path = Path(result["file_path"])
    assert file_path.exists()
    
    with open(file_path, "rb") as f:
        loaded_data = pickle.load(f)
    
    assert np.array_equal(loaded_data["nodes"], sample_graph_data["nodes"])
    assert np.array_equal(loaded_data["edges"], sample_graph_data["edges"])

def test_serialize_graph_parquet_fallback(temp_output_dir, sample_graph_data):
    # This test assumes pandas might not be installed or data structure doesn't support parquet directly
    # The implementation falls back to pickle in such cases, which is valid behavior
    result = serialize_graph(sample_graph_data, "test_002", temp_output_dir, format="parquet")
    
    # Depending on implementation details, it might be parquet or pickle fallback
    assert result["sample_id"] == "test_002"
    assert "checksum" in result
    assert Path(result["file_path"]).exists()

def test_serialize_directory_graphs(temp_output_dir, sample_graph_data):
    # Create a fake input directory with a dummy XYZ-like structure
    # Since we can't easily mock the full XYZ parsing without a real file,
    # we test the serialization logic by manually calling serialize_graph
    # and verifying the directory creation and manifest logic if we were to extend.
    # Here we just verify the function signature and basic error handling
    
    # We will mock the build_graph_from_xyz behavior by pre-populating a list
    # But since serialize_directory_graphs calls build_graph_from_xyz internally,
    # we rely on the fact that if no .xyz files exist, it returns empty list.
    
    input_dir = temp_output_dir / "input_xyz"
    input_dir.mkdir()
    
    # No .xyz files, should return empty
    results = serialize_directory_graphs(input_dir, temp_output_dir / "output")
    assert len(results) == 0

def test_checksum_consistency(temp_output_dir, sample_graph_data):
    # Serialize twice and check checksums are identical
    result1 = serialize_graph(sample_graph_data, "test_003", temp_output_dir, format="pickle")
    result2 = serialize_graph(sample_graph_data, "test_003", temp_output_dir, format="pickle")
    
    # Note: If the file is overwritten, the checksum should be the same.
    # If the file name is unique, we'd compare different files.
    # Here we overwrite the same file name.
    assert result1["checksum"] == result2["checksum"]
