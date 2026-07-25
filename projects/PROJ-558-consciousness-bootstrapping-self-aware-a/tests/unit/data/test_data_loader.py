import json
import os
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from data_loader import (
    compute_checksum,
    load_manifest,
    save_manifest,
    fetch_gsm8k,
    fetch_mmlu,
    save_dataset_and_manifest,
    data_path_str,
    RAW_DIR,
    MANIFEST_PATH
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for testing."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path / "data"

@pytest.fixture
def mock_manifest(temp_data_dir):
    """Create a mock manifest file."""
    manifest_path = temp_data_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump({}, f)
    return temp_data_dir

def test_compute_checksum(temp_data_dir):
    """Test checksum computation."""
    test_file = temp_data_dir / "test.txt"
    test_file.write_text("test content")
    
    checksum = compute_checksum(test_file)
    assert len(checksum) == 64  # SHA-256 produces 64 hex characters
    assert all(c in '0123456789abcdef' for c in checksum)

def test_load_manifest_empty(temp_data_dir):
    """Test loading an empty manifest."""
    manifest_path = temp_data_dir / "manifest.json"
    manifest_path.write_text("{}")
    
    manifest = load_manifest()
    assert manifest == {}

def test_load_manifest_with_data(temp_data_dir):
    """Test loading a manifest with data."""
    manifest_path = temp_data_dir / "manifest.json"
    test_data = {"file1.json": {"type": "test", "checksum": "abc123"}}
    with open(manifest_path, "w") as f:
        json.dump(test_data, f)
    
    manifest = load_manifest()
    assert manifest == test_data

def test_save_manifest(temp_data_dir):
    """Test saving a manifest."""
    test_manifest = {"file1.json": {"type": "test", "checksum": "abc123"}}
    save_manifest(test_manifest)
    
    manifest = load_manifest()
    assert manifest == test_manifest

@patch('data_loader.load_dataset')
def test_fetch_gsm8k(mock_load_dataset, temp_data_dir, mock_manifest):
    """Test fetching GSM8K dataset."""
    # Mock the dataset
    mock_dataset = MagicMock()
    mock_dataset.__iter__ = lambda self: iter([
        {"question": "What is 2+2?", "answer": "4"},
        {"question": "What is 3+3?", "answer": "6"}
    ])
    mock_load_dataset.return_value = mock_dataset
    
    # Update paths to use temp directory
    original_raw_dir = RAW_DIR
    original_manifest_path = MANIFEST_PATH
    
    try:
        import data_loader
        data_loader.RAW_DIR = temp_data_dir / "raw"
        data_loader.MANIFEST_PATH = temp_data_dir / "manifest.json"
        
        fetch_gsm8k()
        
        # Verify the file was created
        output_path = temp_data_dir / "raw" / "gsm8k.json"
        assert output_path.exists()
        
        # Verify content
        with open(output_path, "r") as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["question"] == "What is 2+2?"
        
        # Verify manifest was updated
        manifest = load_manifest()
        assert "gsm8k.json" in manifest
        assert manifest["gsm8k.json"]["type"] == "evaluation"
        
    finally:
        # Restore original paths
        data_loader.RAW_DIR = original_raw_dir
        data_loader.MANIFEST_PATH = original_manifest_path

@patch('data_loader.load_dataset')
def test_fetch_mmlu(mock_load_dataset, temp_data_dir, mock_manifest):
    """Test fetching MMLU dataset."""
    # Mock the dataset
    mock_dataset = MagicMock()
    mock_dataset.__iter__ = lambda self: iter([
        {"question": "What is the capital of France?", "answer": "Paris", "subject": "geography"},
        {"question": "What is 2+2?", "answer": "4", "subject": "math"}
    ])
    mock_load_dataset.return_value = mock_dataset
    
    # Update paths to use temp directory
    original_raw_dir = RAW_DIR
    original_manifest_path = MANIFEST_PATH
    
    try:
        import data_loader
        data_loader.RAW_DIR = temp_data_dir / "raw"
        data_loader.MANIFEST_PATH = temp_data_dir / "manifest.json"
        
        fetch_mmlu()
        
        # Verify the file was created
        output_path = temp_data_dir / "raw" / "mmlu.json"
        assert output_path.exists()
        
        # Verify content
        with open(output_path, "r") as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["subject"] == "geography"
        
        # Verify manifest was updated
        manifest = load_manifest()
        assert "mmlu.json" in manifest
        assert manifest["mmlu.json"]["type"] == "evaluation"
        
    finally:
        # Restore original paths
        data_loader.RAW_DIR = original_raw_dir
        data_loader.MANIFEST_PATH = original_manifest_path

def test_data_path_str():
    """Test that data_path_str returns the correct path."""
    path = data_path_str()
    assert isinstance(path, str)
    assert "data" in path

def test_save_dataset_and_manifest(temp_data_dir, mock_manifest):
    """Test saving a dataset and updating manifest."""
    test_data = [
        {"id": 1, "value": "test1"},
        {"id": 2, "value": "test2"}
    ]
    
    # Update paths to use temp directory
    original_raw_dir = RAW_DIR
    original_manifest_path = MANIFEST_PATH
    
    try:
        import data_loader
        data_loader.RAW_DIR = temp_data_dir / "raw"
        data_loader.MANIFEST_PATH = temp_data_dir / "manifest.json"
        
        save_dataset_and_manifest("test_dataset", test_data, "test")
        
        # Verify the file was created
        output_path = temp_data_dir / "raw" / "test_dataset.json"
        assert output_path.exists()
        
        # Verify content
        with open(output_path, "r") as f:
            data = json.load(f)
        assert data == test_data
        
        # Verify manifest was updated
        manifest = load_manifest()
        assert "test_dataset.json" in manifest
        assert manifest["test_dataset.json"]["type"] == "test"
        
    finally:
        # Restore original paths
        data_loader.RAW_DIR = original_raw_dir
        data_loader.MANIFEST_PATH = original_manifest_path
