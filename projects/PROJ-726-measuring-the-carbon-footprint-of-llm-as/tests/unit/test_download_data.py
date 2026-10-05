import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download_data import (
    fetch_codexglue_dataset,
    compute_file_hash,
    validate_sample_size,
    save_dataset,
    validate_checksum
)

@pytest.fixture
def mock_dataset_iterator():
    """Mock iterator that yields fake CodeXGLUE items."""
    return iter([
        {"source": "def add(a, b): pass", "target": "return a + b"},
        {"source": "def sub(a, b): pass", "target": "return a - b"},
        {"source": "def mul(a, b): pass", "target": "return a * b"},
    ])

@patch("download_data.load_dataset")
def test_fetch_codexglue_dataset_success(mock_load_dataset, mock_dataset_iterator):
    """Test successful fetching of the dataset."""
    mock_load_dataset.return_value.__iter__ = MagicMock(return_value=mock_dataset_iterator)
    
    samples, reason = fetch_codexglue_dataset(sample_size=10)
    
    assert len(samples) == 3
    assert samples[0]["prompt_id"] == "codexglue_0000"
    assert samples[0]["prompt"] == "def add(a, b): pass"
    assert samples[0]["target_code"] == "return a + b"
    assert reason == "Dataset exhausted before reaching target size (only 3 valid samples available)."

def test_validate_sample_size():
    """Test sample size validation logic."""
    # Empty list
    assert not validate_sample_size([], 10)
    
    # Less than target but > 0
    assert validate_sample_size([1, 2], 10)
    
    # Meets target
    assert validate_sample_size([1] * 10, 10)

def test_compute_file_hash(tmp_path):
    """Test file hash computation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")
    
    hash_val = compute_file_hash(test_file)
    assert len(hash_val) == 64  # SHA-256 hex length
    assert hash_val == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

def test_save_dataset(tmp_path):
    """Test saving dataset to JSON."""
    samples = [
        {"prompt_id": "001", "prompt": "test", "target_code": "code"}
    ]
    output_path = tmp_path / "output.json"
    
    save_dataset(samples, output_path)
    
    assert output_path.exists()
    with open(output_path, "r") as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]["prompt_id"] == "001"

def test_validate_checksum(tmp_path):
    """Test checksum validation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test data")
    
    assert validate_checksum(test_file)
    
    assert not validate_checksum(tmp_path / "nonexistent.txt")