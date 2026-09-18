"""
Unit tests for src/loader.py
"""
import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

from src.loader import (
    get_snap_dataset_list,
    load_snap_graph_from_edgelist,
    generate_synthetic_graph,
    fetch_snap_dataset,
    load_real_data
)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "raw"
        state_dir = Path(tmpdir) / "state"
        raw_dir.mkdir()
        state_dir.mkdir()
        yield {
            "raw": raw_dir,
            "state": state_dir,
            "tmpdir": Path(tmpdir)
        }

def test_get_snap_dataset_list():
    """Test that we get a non-empty list of datasets."""
    datasets = get_snap_dataset_list()
    assert len(datasets) > 0
    assert isinstance(datasets, list)
    # Check a few expected datasets
    assert "email-Eu-core.txt" in datasets
    assert "ca-AstroPh.txt" in datasets

def test_generate_synthetic_graph_ba():
    """Test Barabási-Albert graph generation."""
    G = generate_synthetic_graph(100, "ba", m=2)
    assert G.number_of_nodes() == 100
    assert G.number_of_edges() > 0

def test_generate_synthetic_graph_er():
    """Test Erdos-Renyi graph generation."""
    G = generate_synthetic_graph(50, "er", p=0.1)
    assert G.number_of_nodes() == 50
    assert G.number_of_edges() > 0

def test_generate_synthetic_graph_ring():
    """Test ring graph generation."""
    G = generate_synthetic_graph(20, "ring")
    assert G.number_of_nodes() == 20
    # Ring graph has exactly n edges
    assert G.number_of_edges() == 20

def test_load_snap_graph_from_edgelist_plain():
    """Test loading a plain text edgelist."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("0 1\n")
        f.write("1 2\n")
        f.write("2 3\n")
        temp_path = Path(f.name)
    
    try:
        G = load_snap_graph_from_eddelist(temp_path)
        assert G is not None
        assert G.number_of_nodes() == 4
        assert G.number_of_edges() == 3
    finally:
        os.unlink(temp_path)

def test_load_snap_graph_from_edgelist_gz(temp_dirs):
    """Test loading a gzipped edgelist."""
    import gzip
    
    gz_path = temp_dirs["raw"] / "test.txt.gz"
    with gzip.open(gz_path, 'wt') as f:
        f.write("# Comment line\n")
        f.write("0 1\n")
        f.write("1 2\n")
    
    G = load_snap_graph_from_edgelist(gz_path)
    assert G is not None
    assert G.number_of_nodes() == 3
    assert G.number_of_edges() == 2

@patch('src.loader.requests.get')
def test_fetch_snap_dataset(mock_get, temp_dirs):
    """Test fetching a dataset from SNAP."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b"0 1\n1 2\n"]
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    
    result = fetch_snap_dataset("test.txt", temp_dirs["raw"])
    
    assert result is not None
    assert result.exists()
    mock_get.assert_called_once()

def test_load_real_data_with_insufficient_files(temp_dirs):
    """Test load_real_data when file count < minimum."""
    config = {
        "paths": {
            "raw_data": str(temp_dirs["raw"]),
            "state": str(temp_dirs["state"])
        },
        "thresholds": {
            "min_files": 10
        }
    }
    
    # Create only 3 files
    for i in range(3):
        (temp_dirs["raw"] / f"test_{i}.txt").touch()
    
    result = load_real_data(config)
    
    assert result["data_availability_flag"] == False
    assert result["file_count"] == 3
    
    # Check state file was written
    state_file = temp_dirs["state"] / "data_availability.json"
    assert state_file.exists()
    
    with open(state_file) as f:
        state_data = json.load(f)
    
    assert state_data["data_availability_flag"] == False
    assert state_data["file_count"] == 3
    assert "warning" in state_data

def test_load_real_data_with_sufficient_files(temp_dirs):
    """Test load_real_data when file count >= minimum."""
    config = {
        "paths": {
            "raw_data": str(temp_dirs["raw"]),
            "state": str(temp_dirs["state"])
        },
        "thresholds": {
            "min_files": 3
        }
    }
    
    # Create 5 files
    for i in range(5):
        (temp_dirs["raw"] / f"test_{i}.txt").touch()
    
    result = load_real_data(config)
    
    assert result["data_availability_flag"] == True
    assert result["file_count"] == 5

def test_load_real_data_no_synthetic_fallback(temp_dirs):
    """
    Verify that load_real_data does NOT generate synthetic data
    when files are missing.
    """
    config = {
        "paths": {
            "raw_data": str(temp_dirs["raw"]),
            "state": str(temp_dirs["state"])
        },
        "thresholds": {
            "min_files": 10
        }
    }
    
    # No files created
    result = load_real_data(config)
    
    # Should return the actual count (0), not a synthetic count
    assert result["file_count"] == 0
    assert result["data_availability_flag"] == False
    
    # Verify no synthetic files were created
    files = list(temp_dirs["raw"].glob("*"))
    assert len(files) == 0
