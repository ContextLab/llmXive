"""
Unit tests for data_loader.py
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from datasets import Dataset

from code.data_loader import (
    LoudFailureError,
    verify_checksum,
    fetch_advbench,
    fetch_hf4,
    fetch_taxonomy,
    save_jsonl_file,
    load_jsonl_file
)
from code.config import get_path


class TestVerifyChecksum:
    def test_verify_checksum_success(self, tmp_path):
        """Test checksum verification with matching hash."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        content = "test content"
        test_file.write_text(content)
        
        # Calculate expected checksum
        import hashlib
        expected = hashlib.sha256(content.encode()).hexdigest()
        
        # Verify
        assert verify_checksum(str(test_file), expected) is True

    def test_verify_checksum_failure(self, tmp_path):
        """Test checksum verification with mismatched hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Wrong checksum
        assert verify_checksum(str(test_file), "wrong_checksum") is False


class TestSaveLoadJsonl:
    def test_save_and_load_jsonl(self, tmp_path):
        """Test saving and loading JSONL files."""
        test_file = tmp_path / "test.jsonl"
        test_data = [
            {"id": 1, "text": "hello"},
            {"id": 2, "text": "world"}
        ]
        
        save_jsonl_file(test_data, test_file)
        
        loaded_data = load_jsonl_file(test_file)
        
        assert len(loaded_data) == 2
        assert loaded_data[0]["id"] == 1
        assert loaded_data[0]["text"] == "hello"
        assert loaded_data[1]["id"] == 2
        assert loaded_data[1]["text"] == "world"


@patch('code.data_loader.load_dataset')
def test_fetch_advbench_success(mock_load_dataset, tmp_path):
    """Test successful AdvBench fetch."""
    # Mock dataset
    mock_dataset = MagicMock(spec=Dataset)
    mock_dataset.__iter__ = MagicMock(return_value=iter([
        {"text": "adv_test_1", "label": "attack"},
        {"text": "adv_test_2", "label": "attack"}
    ]))
    mock_load_dataset.return_value = mock_dataset
    
    # Create output path
    output_path = tmp_path / "advbench.jsonl"
    
    # Fetch
    data = fetch_advbench(output_path)
    
    # Verify
    assert len(data) == 2
    assert data[0]["text"] == "adv_test_1"
    assert output_path.exists()
    
    # Verify file content
    with open(output_path, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 2


@patch('code.data_loader.load_dataset')
def test_fetch_advbench_empty(mock_load_dataset):
    """Test AdvBench fetch with empty dataset."""
    mock_dataset = MagicMock(spec=Dataset)
    mock_dataset.__iter__ = MagicMock(return_value=iter([]))
    mock_load_dataset.return_value = mock_dataset
    
    with pytest.raises(LoudFailureError, match="AdvBench dataset is empty"):
        fetch_advbench()


@patch('code.data_loader.load_dataset')
def test_fetch_advbench_failure(mock_load_dataset):
    """Test AdvBench fetch failure."""
    mock_load_dataset.side_effect = Exception("Network error")
    
    with pytest.raises(LoudFailureError, match="Failed to fetch AdvBench dataset"):
        fetch_advbench()


@patch('code.data_loader.load_dataset')
def test_fetch_hf4_success(mock_load_dataset, tmp_path):
    """Test successful HF4 fetch."""
    # Mock dataset
    mock_dataset = MagicMock(spec=Dataset)
    mock_dataset.__iter__ = MagicMock(return_value=iter([
        {"text": "safe_test_1", "label": "benign"},
        {"text": "safe_test_2", "label": "benign"}
    ]))
    mock_load_dataset.return_value = mock_dataset
    
    output_path = tmp_path / "hf4.jsonl"
    data = fetch_hf4(output_path)
    
    assert len(data) == 2
    assert data[0]["text"] == "safe_test_1"
    assert output_path.exists()


@patch('code.data_loader.load_dataset')
def test_fetch_hf4_empty(mock_load_dataset):
    """Test HF4 fetch with empty dataset."""
    mock_dataset = MagicMock(spec=Dataset)
    mock_dataset.__iter__ = MagicMock(return_value=iter([]))
    mock_load_dataset.return_value = mock_dataset
    
    with pytest.raises(LoudFailureError, match="HF4 dataset is empty"):
        fetch_hf4()


@patch('code.data_loader.load_dataset')
def test_fetch_hf4_failure(mock_load_dataset):
    """Test HF4 fetch failure."""
    mock_load_dataset.side_effect = Exception("Network error")
    
    with pytest.raises(LoudFailureError, match="Failed to fetch HF4 dataset"):
        fetch_hf4()


@patch('code.data_loader.load_dataset')
def test_fetch_taxonomy_success(mock_load_dataset, tmp_path):
    """Test successful taxonomy fetch."""
    mock_dataset = MagicMock(spec=Dataset)
    mock_dataset.__iter__ = MagicMock(return_value=iter([
        {"id": "cat1", "name": "Category 1"},
        {"id": "cat2", "name": "Category 2"}
    ]))
    mock_load_dataset.return_value = mock_dataset
    
    output_path = tmp_path / "taxonomy.json"
    data = fetch_taxonomy(output_path)
    
    assert len(data) == 2
    assert data[0]["id"] == "cat1"
    assert output_path.exists()
    
    # Verify JSON format
    with open(output_path, 'r') as f:
        loaded = json.load(f)
        assert isinstance(loaded, list)


@patch('code.data_loader.load_dataset')
def test_fetch_taxonomy_empty(mock_load_dataset):
    """Test taxonomy fetch with empty dataset."""
    mock_dataset = MagicMock(spec=Dataset)
    mock_dataset.__iter__ = MagicMock(return_value=iter([]))
    mock_load_dataset.return_value = mock_dataset
    
    with pytest.raises(LoudFailureError, match="Taxonomy dataset is empty"):
        fetch_taxonomy()


@patch('code.data_loader.load_dataset')
def test_fetch_taxonomy_failure(mock_load_dataset):
    """Test taxonomy fetch failure."""
    mock_load_dataset.side_effect = Exception("Network error")
    
    with pytest.raises(LoudFailureError, match="Failed to fetch taxonomy"):
        fetch_taxonomy()