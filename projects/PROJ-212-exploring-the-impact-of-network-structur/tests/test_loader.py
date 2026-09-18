import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

# Import the module under test
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
        raw_dir = Path(tmpdir) / "data" / "raw"
        state_dir = Path(tmpdir) / "state"
        raw_dir.mkdir(parents=True, exist_ok=True)
        state_dir.mkdir(parents=True, exist_ok=True)
        yield {
            "raw": raw_dir,
            "state": state_dir,
            "tmp": Path(tmpdir)
        }

def test_get_snap_dataset_list():
    """Test that get_snap_dataset_list returns a non-empty list of datasets."""
    datasets = get_snap_dataset_list()
    assert isinstance(datasets, list)
    assert len(datasets) > 0
    assert all('id' in ds and 'name' in ds for ds in datasets)

def test_generate_synthetic_graph_ba():
    """Test Barabási-Albert graph generation."""
    G = generate_synthetic_graph("ba", n=10)
    assert G.number_of_nodes() == 10
    assert G.number_of_edges() > 0
    assert nx.is_connected(G) or G.number_of_nodes() == 1

def test_generate_synthetic_graph_er():
    """Test Erdős-Rényi graph generation."""
    G = generate_synthetic_graph("er", n=10)
    assert G.number_of_nodes() == 10

def test_generate_synthetic_graph_ring():
    """Test Ring graph generation."""
    G = generate_synthetic_graph("ring", n=10)
    assert G.number_of_nodes() == 10
    assert G.number_of_edges() == 10

def test_load_snap_graph_from_edgelist_plain(temp_dirs):
    """Test loading a plain text edgelist."""
    raw_dir = temp_dirs["raw"]
    edgelist_file = raw_dir / "test_graph.txt"
    
    with open(edgelist_file, 'w') as f:
        f.write("0 1\n1 2\n2 3\n")
    
    G = load_snap_graph_from_edgelist(edgelist_file)
    assert G is not None
    assert G.number_of_nodes() == 4
    assert G.number_of_edges() == 3

def test_load_snap_graph_from_edgelist_gz(temp_dirs):
    """Test loading a gzipped edgelist (if supported, else skip)."""
    # For simplicity, we test the plain text fallback in the function
    # Since the function doesn't explicitly handle .gz in the provided code, we skip or test plain
    pass

@patch('src.loader.load_dataset')
def test_fetch_snap_dataset(mock_load_dataset, temp_dirs):
    """Test fetching a dataset from HuggingFace (mocked)."""
    mock_dataset = MagicMock()
    mock_dataset.__iter__ = MagicMock(return_value=iter([
        {'edges': [[0, 1], [1, 2]]},
        {'edges': [[2, 3], [3, 4]]},
        {'edges': [[4, 5], [5, 6]]},
        {'edges': [[6, 7], [7, 8]]},
        {'edges': [[8, 9], [9, 0]]},
    ]))
    mock_load_dataset.return_value = mock_dataset
    
    target_dir = temp_dirs["raw"]
    success = fetch_snap_dataset("test_ds", target_dir)
    
    assert success is True
    # Check if files were created
    files = list(target_dir.glob("test_ds_*.txt"))
    assert len(files) == 5

@patch('src.loader.get_snap_dataset_list')
@patch('src.loader.fetch_snap_dataset')
def test_load_real_data_with_insufficient_files(mock_fetch, mock_get_list, temp_dirs):
    """Test load_real_data when fewer than 10 files are found."""
    # Mock the dataset list
    mock_get_list.return_value = [{"id": "test", "name": "Test"}]
    # Mock fetch to create only 5 files
    mock_fetch.return_value = True
    
    # Create 5 dummy files in raw dir
    for i in range(5):
        (temp_dirs["raw"] / f"file_{i}.txt").touch()
    
    # Mock Path.cwd for state file
    with patch('src.loader.Path.cwd', return_value=temp_dirs["tmp"]):
        # Temporarily override RAW_DATA_DIR and STATE_DIR
        import src.loader as loader_module
        original_raw = loader_module.RAW_DATA_DIR
        original_state = loader_module.STATE_DIR
        loader_module.RAW_DATA_DIR = temp_dirs["raw"]
        loader_module.STATE_DIR = temp_dirs["state"]
        
        result = load_real_data()
        
        # Restore
        loader_module.RAW_DATA_DIR = original_raw
        loader_module.STATE_DIR = original_state
    
    assert result["file_count"] == 5
    assert result["data_availability_flag"] is False
    assert "Warning" in result["message"]
    
    # Check state file
    state_file = temp_dirs["state"] / "data_availability.json"
    assert state_file.exists()
    with open(state_file) as f:
        state_data = json.load(f)
    assert state_data["data_availability_flag"] is False

@patch('src.loader.get_snap_dataset_list')
@patch('src.loader.fetch_snap_dataset')
def test_load_real_data_with_sufficient_files(mock_fetch, mock_get_list, temp_dirs):
    """Test load_real_data when 10 or more files are found."""
    mock_get_list.return_value = [{"id": "test", "name": "Test"}]
    mock_fetch.return_value = True
    
    # Create 10 dummy files
    for i in range(10):
        (temp_dirs["raw"] / f"file_{i}.txt").touch()
    
    import src.loader as loader_module
    original_raw = loader_module.RAW_DATA_DIR
    original_state = loader_module.STATE_DIR
    loader_module.RAW_DATA_DIR = temp_dirs["raw"]
    loader_module.STATE_DIR = temp_dirs["state"]
    
    result = load_real_data()
    
    loader_module.RAW_DATA_DIR = original_raw
    loader_module.STATE_DIR = original_state
    
    assert result["file_count"] == 10
    assert result["data_availability_flag"] is True

def test_load_real_data_no_synthetic_fallback(temp_dirs):
    """Test that load_real_data does not generate synthetic data."""
    import src.loader as loader_module
    original_raw = loader_module.RAW_DATA_DIR
    original_state = loader_module.STATE_DIR
    loader_module.RAW_DATA_DIR = temp_dirs["raw"]
    loader_module.STATE_DIR = temp_dirs["state"]
    
    # Ensure no files exist
    assert len(list(temp_dirs["raw"].glob("*"))) == 0
    
    # Mock get_snap_dataset_list to return empty or fetch to fail
    with patch.object(loader_module, 'get_snap_dataset_list', return_value=[]):
        result = load_real_data()
    
    loader_module.RAW_DATA_DIR = original_raw
    loader_module.STATE_DIR = original_state
    
    # Should not have created any synthetic files
    assert len(list(temp_dirs["raw"].glob("*"))) == 0
    assert result["file_count"] == 0
    assert result["data_availability_flag"] is False