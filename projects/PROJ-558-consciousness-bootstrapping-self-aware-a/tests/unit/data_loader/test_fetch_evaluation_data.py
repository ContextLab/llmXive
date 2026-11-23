import json
import os
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the functions to test
from data_loader import (
    fetch_gsm8k,
    fetch_mmlu,
    compute_checksum,
    load_manifest,
    save_manifest,
    RAW_DIR,
    MANIFEST_PATH
)
from utils.logging import DataLoadError

@pytest.fixture
def mock_hf_dataset():
    """Mock a HuggingFace dataset object."""
    mock_ds = MagicMock()
    mock_ds.to_list.return_value = [
        {"question": "Test question", "answer": "Test answer", "steps": []}
    ]
    return mock_ds

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path

def test_fetch_gsm8k_success(mock_hf_dataset, temp_dir, monkeypatch):
    """Test successful fetching of GSM8K dataset."""
    # Change directory to temp_dir to simulate project root
    monkeypatch.chdir(temp_dir)
    
    # Mock load_dataset to return our mock dataset
    with patch('data_loader.load_dataset', return_value=mock_hf_dataset):
        with patch('data_loader.RAW_DIR', new=temp_dir / "data" / "raw"):
            with patch('data_loader.MANIFEST_PATH', new=temp_dir / "data" / "manifest.json"):
                result_path = fetch_gsm8k()
                
                assert result_path.exists()
                assert result_path.name == "gsm8k.json"
                
                # Verify content
                with open(result_path, "r") as f:
                    data = json.load(f)
                    assert len(data) == 1
                    assert data[0]["question"] == "Test question"

def test_fetch_mmlu_success(mock_hf_dataset, temp_dir, monkeypatch):
    """Test successful fetching of MMLU dataset."""
    monkeypatch.chdir(temp_dir)
    
    with patch('data_loader.load_dataset', return_value=mock_hf_dataset):
        with patch('data_loader.RAW_DIR', new=temp_dir / "data" / "raw"):
            with patch('data_loader.MANIFEST_PATH', new=temp_dir / "data" / "manifest.json"):
                result_path = fetch_mmlu()
                
                assert result_path.exists()
                assert result_path.name == "mmlu.json"
                
                with open(result_path, "r") as f:
                    data = json.load(f)
                    assert len(data) == 1

def test_fetch_gsm8k_failure(temp_dir, monkeypatch):
    """Test that fetch_gsm8k raises DataLoadError on failure."""
    monkeypatch.chdir(temp_dir)
    
    with patch('data_loader.load_dataset', side_effect=Exception("Network error")):
        with patch('data_loader.RAW_DIR', new=temp_dir / "data" / "raw"):
            with patch('data_loader.MANIFEST_PATH', new=temp_dir / "data" / "manifest.json"):
                with pytest.raises(DataLoadError, match="Failed to load GSM8K dataset"):
                    fetch_gsm8k()

def test_fetch_mmlu_failure(temp_dir, monkeypatch):
    """Test that fetch_mmlu raises DataLoadError on failure."""
    monkeypatch.chdir(temp_dir)
    
    with patch('data_loader.load_dataset', side_effect=Exception("Network error")):
        with patch('data_loader.RAW_DIR', new=temp_dir / "data" / "raw"):
            with patch('data_loader.MANIFEST_PATH', new=temp_dir / "data" / "manifest.json"):
                with pytest.raises(DataLoadError, match="Failed to load MMLU dataset"):
                    fetch_mmlu()

def test_compute_checksum(temp_dir):
    """Test checksum computation."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Hello, World!")
    
    checksum = compute_checksum(test_file)
    assert len(checksum) == 64  # SHA-256 hex length
    assert checksum == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

def test_manifest_lifecycle(temp_dir, monkeypatch):
    """Test saving and loading manifest."""
    monkeypatch.chdir(temp_dir)
    manifest_path = temp_dir / "data" / "manifest.json"
    
    initial_manifest = {"test": {"value": 1}}
    save_manifest(initial_manifest)
    
    loaded = load_manifest()
    assert loaded == initial_manifest
    
    # Update and save again
    initial_manifest["test2"] = {"value": 2}
    save_manifest(initial_manifest)
    
    loaded_again = load_manifest()
    assert loaded_again["test2"]["value"] == 2
