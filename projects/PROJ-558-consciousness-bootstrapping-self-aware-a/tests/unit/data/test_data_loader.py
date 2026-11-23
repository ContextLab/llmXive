import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Adjust imports based on project structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_loader import compute_checksum, load_manifest, save_manifest, fetch_gsm8k, fetch_mmlu, save_dataset_and_manifest, DATA_DIR, MANIFEST_PATH
from utils.logging import DataLoadError

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

def test_compute_checksum(temp_dir):
    """Test that compute_checksum returns a valid hex string."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("hello world")
    checksum = compute_checksum(test_file)
    assert len(checksum) == 64  # SHA-256 hex length
    assert all(c in "0123456789abcdef" for c in checksum)

def test_load_manifest_empty(temp_dir, monkeypatch):
    """Test loading manifest when file doesn't exist."""
    monkeypatch.setattr("code.data_loader.MANIFEST_PATH", temp_dir / "nonexistent.json")
    manifest = load_manifest()
    assert manifest == {}

def test_save_manifest(temp_dir, monkeypatch):
    """Test saving manifest."""
    manifest_path = temp_dir / "manifest.json"
    monkeypatch.setattr("code.data_loader.MANIFEST_PATH", manifest_path)
    
    test_data = {"key": "value"}
    save_manifest(test_data)
    
    assert manifest_path.exists()
    with open(manifest_path) as f:
        loaded = json.load(f)
    assert loaded == test_data

def test_fetch_gsm8k_failure():
    """Test that fetch_gsm8k raises DataLoadError on failure."""
    with patch("code.data_loader.load_dataset") as mock_load:
        mock_load.side_effect = Exception("Network error")
        with pytest.raises(DataLoadError):
            fetch_gsm8k()

def test_fetch_mmlu_failure():
    """Test that fetch_mmlu raises DataLoadError on failure."""
    with patch("code.data_loader.load_dataset") as mock_load:
        mock_load.side_effect = Exception("Network error")
        with pytest.raises(DataLoadError):
            fetch_mmlu()

def test_save_dataset_and_manifest(temp_dir, monkeypatch):
    """Test saving dataset and updating manifest."""
    # Setup paths in temp dir
    data_dir = temp_dir / "raw"
    manifest_path = temp_dir / "manifest.json"
    monkeypatch.setattr("code.data_loader.DATA_DIR", data_dir)
    monkeypatch.setattr("code.data_loader.MANIFEST_PATH", manifest_path)

    mock_data = [{"question": "2+2?", "answer": "4"}]
    save_dataset_and_manifest("test_dataset", mock_data)

    # Check file exists
    json_file = data_dir / "test_dataset.json"
    assert json_file.exists()

    # Check content
    with open(json_file) as f:
        loaded_data = json.load(f)
    assert loaded_data == mock_data

    # Check manifest
    assert manifest_path.exists()
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    assert "test_dataset" in manifest
    assert manifest["test_dataset"]["type"] == "evaluation"
    assert "checksum" in manifest["test_dataset"]
    assert "size_bytes" in manifest["test_dataset"]
    assert "created_at" in manifest["test_dataset"]