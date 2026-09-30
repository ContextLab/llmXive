import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Import the module to test
# Note: In a real execution environment, the path would be relative to the project root
# For unit tests, we assume the code/ directory is in PYTHONPATH
from download_data import (
    compute_file_hash,
    validate_sample_size,
    verify_baseline_exists,
    save_dataset,
    validate_checksum
)

def test_compute_file_hash():
    """Test that file hashing works correctly."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("Hello World")
        temp_path = f.name

    try:
        hash_val = compute_file_hash(temp_path)
        assert len(hash_val) == 64  # SHA256 hex length
        assert isinstance(hash_val, str)
    finally:
        os.unlink(temp_path)

def test_validate_sample_size_exceeds_target():
    """Test that sample size is capped at target."""
    result = validate_sample_size(300, target_size=200)
    assert result == 200

def test_validate_sample_size_within_target():
    """Test that sample size is kept as is if within target."""
    result = validate_sample_size(150, target_size=200)
    assert result == 150

def test_verify_baseline_exists_true():
    """Test baseline verification when file exists."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
        f.write(b"{}")
        temp_path = f.name

    try:
        result = verify_baseline_exists(temp_path)
        assert result is True
    finally:
        os.unlink(temp_path)

def test_verify_baseline_exists_false():
    """Test baseline verification when file does not exist."""
    result = verify_baseline_exists("/non/existent/path.json")
    assert result is False

def test_save_dataset_creates_file():
    """Test that save_dataset creates the output file."""
    # Mock dataset iterator
    mock_data = [
        {"source": "print('hello')", "target": "print('world')"},
        {"source": "x = 1", "target": "y = 2"}
    ]
    mock_dataset = iter(mock_data)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test.json")
        
        # Mock the dataset object to behave like a streaming iterator
        with patch('download_data.load_dataset', return_value=mock_dataset):
            # We need to mock the dataset object itself to pass to save_dataset
            # The save_dataset function iterates over the dataset
            save_dataset(mock_dataset, output_path, sample_size=2)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert len(data) == 2
            assert "prompt_id" in data[0]
            assert "source" in data[0]
