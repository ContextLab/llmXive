"""
Unit tests for code/data/download.py

These tests verify the logic of T015 without requiring network access
(by mocking the dataset loading).
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.download import load_feasibility_report, fetch_dataset_subset, write_chunks_to_disk

@pytest.fixture
def mock_feasibility_report(tmp_path):
    """Create a mock feasibility report."""
    report = {
        "capped_N": 100,
        "scope_reduction": {"disable_cross_language": False},
        "status": "feasible"
    }
    report_path = tmp_path / "data" / "results" / "feasibility_report_v2.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f)
    return report_path

def test_load_feasibility_report_success(mock_feasibility_report, tmp_path):
    """Test loading a valid feasibility report."""
    # Mock get_project_root to return tmp_path parent
    with patch('data.download.get_project_root', return_value=tmp_path.parent):
        report = load_feasibility_report()
        assert report["capped_N"] == 100
        assert report["status"] == "feasible"

def test_load_feasibility_report_missing(mock_feasibility_report, tmp_path):
    """Test handling of missing feasibility report."""
    # Rename the file to simulate missing
    missing_path = tmp_path / "data" / "results" / "nonexistent.json"
    with patch('data.download.get_project_root', return_value=tmp_path.parent):
        with patch('data.download.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                load_feasibility_report()

@patch('data.download.load_dataset')
def test_fetch_dataset_subset(mock_load_dataset):
    """Test fetching dataset subset with mocked dataset."""
    # Mock the dataset iterator
    mock_item = {"content": "print('hello')", "path": "test.py", "language": "Python"}
    mock_iterator = iter([mock_item] * 10)
    
    mock_ds = MagicMock()
    mock_ds.filter.return_value.take.return_value = mock_iterator
    mock_load_dataset.return_value = mock_ds
    
    chunks = fetch_dataset_subset(["Python"], 10)
    
    assert len(chunks) == 10
    assert all(c['language'] == 'Python' for c in chunks)
    assert all('chunk_id' in c for c in chunks)

@patch('data.download.load_dataset')
def test_fetch_dataset_subset_empty(mock_load_dataset):
    """Test fetching when dataset returns empty."""
    mock_ds = MagicMock()
    mock_ds.filter.return_value.take.return_value = iter([])
    mock_load_dataset.return_value = mock_ds
    
    chunks = fetch_dataset_subset(["Python"], 10)
    assert len(chunks) == 0

def test_write_chunks_to_disk(tmp_path):
    """Test writing chunks to disk."""
    chunks = [
        {"chunk_id": "1", "language": "Python", "content": "x=1", "path": "a.py"},
        {"chunk_id": "2", "language": "Java", "content": "int x=1;", "path": "b.java"}
    ]
    
    root = tmp_path / "project"
    root.mkdir()
    
    paths = write_chunks_to_disk(chunks, ["Python", "Java"], root)
    
    # Check files exist
    assert os.path.exists(paths["Python"])
    assert os.path.exists(paths["Java"])
    
    # Check content
    with open(paths["Python"], 'r') as f:
        lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["language"] == "Python"

def test_fetch_dataset_subset_network_error():
    """Test handling of network errors."""
    with patch('data.download.load_dataset') as mock_load:
        mock_load.side_effect = Exception("Network timeout")
        
        with pytest.raises(Exception) as exc_info:
            fetch_dataset_subset(["Python"], 10)
        
        assert "Network timeout" in str(exc_info.value)