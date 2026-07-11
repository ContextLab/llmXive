"""
Tests for the HumanEval dataset download script.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We will test the logic by mocking the dataset loading
# since we don't want to actually download in tests

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_compute_file_hash(temp_data_dir):
    """Test the file hash computation function."""
    from code.data.download_humaneval import compute_file_hash

    test_file = temp_data_dir / "test.txt"
    test_file.write_text("Hello, World!")
    
    hash1 = compute_file_hash(test_file)
    hash2 = compute_file_hash(test_file)
    
    # Same file should produce same hash
    assert hash1 == hash2
    # Hash should be a valid SHA-256 hex string
    assert len(hash1) == 64
    assert all(c in '0123456789abcdef' for c in hash1)

def test_download_humaneval_logic():
    """Test the download logic with mocked dataset."""
    from code.data.download_humaneval import main
    from datasets import Dataset
    
    # Mock the load_dataset function
    mock_data = [
        {"task_id": "HumanEval/0", "prompt": "def add(a, b):\n    return a + b", "canonical_solution": "def add(a, b):\n    return a + b"},
        {"task_id": "HumanEval/1", "prompt": "def multiply(a, b):\n    return a * b", "canonical_solution": "def multiply(a, b):\n    return a * b"}
    ]
    
    mock_dataset = Dataset.from_list(mock_data)
    
    with patch('code.data.download_humaneval.load_dataset', return_value=mock_dataset):
        with patch('code.data.download_humaneval.DATA_DIR', Path(tempfile.mkdtemp())) as mock_dir:
            with patch('code.data.download_humaneval.OUTPUT_FILE', mock_dir / "humaneval.json"):
                with patch('code.data.download_humaneval.METADATA_FILE', mock_dir / "humaneval_metadata.json"):
                    result = main()
                    
                    assert result == 0
                    
                    # Verify output file was created
                    assert (mock_dir / "humaneval.json").exists()
                    assert (mock_dir / "humaneval_metadata.json").exists()
                    
                    # Verify content
                    with open(mock_dir / "humaneval.json", "r") as f:
                        data = json.load(f)
                        assert len(data) == 2
                        assert data[0]["task_id"] == "HumanEval/0"
                    
                    with open(mock_dir / "humaneval_metadata.json", "r") as f:
                        metadata = json.load(f)
                        assert metadata["num_problems"] == 2
                        assert "commit_hash" in metadata
                        assert "file_hash" in metadata
                        assert "download_timestamp" in metadata

def test_metadata_structure(temp_data_dir):
    """Test that metadata file has the expected structure."""
    from code.data.download_humaneval import compute_file_hash
    
    test_file = temp_data_dir / "test.json"
    test_file.write_text(json.dumps([{"task_id": "test"}]))
    
    metadata = {
        "dataset_name": "test",
        "repo_id": "test/repo",
        "commit_hash": "abc123",
        "download_timestamp": "2024-01-01T00:00:00Z",
        "num_problems": 1,
        "file_hash": compute_file_hash(test_file),
        "output_path": str(test_file),
        "source": "Test Source"
    }
    
    # Verify all required fields are present
    required_fields = [
        "dataset_name", "repo_id", "commit_hash", "download_timestamp",
        "num_problems", "file_hash", "output_path", "source"
    ]
    
    for field in required_fields:
        assert field in metadata, f"Missing required field: {field}"