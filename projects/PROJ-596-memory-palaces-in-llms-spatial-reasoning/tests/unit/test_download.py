"""
Unit tests for code/data/download.py.

These tests verify the logic of checksum computation and path handling.
Note: Actual dataset downloads are skipped in unit tests to avoid network calls.
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module to test
# We need to mock the `load_dataset` function to avoid actual downloads
from unittest.mock import patch, MagicMock

# Add parent directory to path if running directly, though usually handled by test runner
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data import download

def test_compute_file_checksum(tmp_path):
    """Test that checksum computation works correctly."""
    # Create a test file
    test_file = tmp_path / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()
    computed_hash = download.compute_file_checksum(test_file)

    assert computed_hash == expected_hash

def test_compute_file_checksum_empty(tmp_path):
    """Test checksum of an empty file."""
    test_file = tmp_path / "empty.txt"
    test_file.write_bytes(b"")

    expected_hash = hashlib.sha256(b"").hexdigest()
    computed_hash = download.compute_file_checksum(test_file)

    assert computed_hash == expected_hash

def test_main_structure(mocked_datasets):
    """
    Test the main function structure with mocked datasets.
    Ensures the script runs without crashing and produces the output file.
    """
    with patch.object(download, 'load_dataset', return_value=MagicMock(keys=lambda: ['train'])):
        with patch.object(download, 'get_dataset_cache_paths', return_value=[mocked_datasets.cache_dir]):
            with patch.object(download, 'DATA_RAW_DIR', mocked_datasets.data_dir):
                with patch.object(download, 'CHECKSUMS_FILE', mocked_datasets.checksum_file):
                    # Create a dummy file in the fake cache to checksum
                    (mocked_datasets.cache_dir / "dummy.txt").write_bytes(b"test")

                    exit_code = download.main()
                    
                    assert exit_code == 0
                    assert mocked_datasets.checksum_file.exists()
                    
                    with open(mocked_datasets.checksum_file, "r") as f:
                        data = json.load(f)
                    
                    assert "datasets" in data
                    assert "babi" in data["datasets"]
                    assert data["datasets"]["babi"]["status"] == "success"

@pytest.fixture
def mocked_datasets(tmp_path):
    """Fixture to create a mock environment for testing."""
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True)
    
    cache_dir = tmp_path / "cache" / "datasets" / "babi" / "task3_10k"
    cache_dir.mkdir(parents=True)
    
    checksum_file = data_dir / "checksums.json"
    
    class MockedDatasets:
        data_dir = data_dir
        cache_dir = cache_dir
        checksum_file = checksum_file
    
    return MockedDatasets
