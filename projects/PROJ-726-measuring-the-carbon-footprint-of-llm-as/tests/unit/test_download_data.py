"""
Unit tests for download_data.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# We need to mock the heavy dependencies to avoid network calls in unit tests
# But we must ensure the logic is correct.

# Mock the datasets library
class MockDatasetItem:
    def __init__(self, source, target):
        self.source = source
        self.target = target
    
    def __getitem__(self, key):
        if key == 'source':
            return self.source
        if key == 'target':
            return self.target
        raise KeyError(key)
    
    def __contains__(self, key):
        return key in ['source', 'target']

class MockDatasetIterator:
    def __init__(self, items, max_count=5):
        self.items = items
        self.count = 0
        self.max_count = max_count
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.count >= self.max_count:
            raise StopIteration
        item = self.items[self.count]
        self.count += 1
        return item

# Mock the load_dataset function
def mock_load_dataset(name, config, split, streaming):
    items = [
        MockDatasetItem("def hello(): pass", "print('hello')"),
        MockDatasetItem("def add(a, b): return a+b", "def add(a, b): return a + b"),
    ]
    return MockDatasetIterator(items, max_count=2)

@pytest.fixture
def mock_datasets(monkeypatch):
    import sys
    from unittest.mock import MagicMock
    datasets_mock = MagicMock()
    datasets_mock.load_dataset = mock_load_dataset
    sys.modules['datasets'] = datasets_mock
    return datasets_mock

def test_validate_sample_size_success():
    from download_data import validate_sample_size
    records = [{"id": 1}, {"id": 2}]
    assert validate_sample_size(records, min_size=1) is True
    assert validate_sample_size(records, min_size=2) is True

def test_validate_sample_size_failure():
    from download_data import validate_sample_size
    records = []
    assert validate_sample_size(records, min_size=1) is False

def test_compute_file_hash(tmp_path):
    from download_data import compute_file_hash
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")
    
    hash1 = compute_file_hash(test_file)
    hash2 = compute_file_hash(test_file)
    
    assert len(hash1) == 64  # SHA256 hex length
    assert hash1 == hash2

def test_save_dataset(mock_datasets, tmp_path, monkeypatch):
    from download_data import save_dataset, validate_sample_size, fetch_codexglue_dataset
    
    # Override the DATA_DIR for this test
    import download_data
    original_dir = download_data.DATA_DIR
    download_data.DATA_DIR = tmp_path
    download_data.OUTPUT_FILE = tmp_path / "test_output.json"
    
    # Patch load_dataset
    monkeypatch.setattr("download_data.load_dataset", mock_load_dataset)
    
    records = fetch_codexglue_dataset()
    assert len(records) == 2
    
    save_dataset(records, download_data.OUTPUT_FILE)
    
    assert download_data.OUTPUT_FILE.exists()
    with open(download_data.OUTPUT_FILE) as f:
        data = json.load(f)
    assert len(data) == 2
    assert "prompt_id" in data[0]
    
    # Restore
    download_data.DATA_DIR = original_dir

def test_validate_checksum_creation(mock_datasets, tmp_path, monkeypatch):
    from download_data import validate_checksum, save_dataset, fetch_codexglue_dataset, compute_file_hash
    import download_data
    
    original_dir = download_data.DATA_DIR
    download_data.DATA_DIR = tmp_path
    download_data.OUTPUT_FILE = tmp_path / "test.json"
    download_data.CHECKSUM_FILE = tmp_path / "checksum.json"
    
    monkeypatch.setattr("download_data.load_dataset", mock_load_dataset)
    
    records = fetch_codexglue_dataset()
    save_dataset(records, download_data.OUTPUT_FILE)
    
    # First run should create checksum
    validate_checksum(records, download_data.CHECKSUM_FILE)
    assert download_data.CHECKSUM_FILE.exists()
    
    # Second run should validate
    validate_checksum(records, download_data.CHECKSUM_FILE)
    
    download_data.DATA_DIR = original_dir

def test_fetch_empty_dataset(mock_datasets, monkeypatch):
    from download_data import fetch_codexglue_dataset
    import download_data
    
    def mock_empty(*args, **kwargs):
        return MockDatasetIterator([], max_count=0)
    
    monkeypatch.setattr("download_data.load_dataset", mock_empty)
    
    with pytest.raises(RuntimeError, match="No valid records found"):
        fetch_codexglue_dataset()