"""
Unit tests for the data download module.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.data.download import DataLoader

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_data_loader_init(temp_dir):
    """Test DataLoader initialization."""
    loader = DataLoader(base_path=temp_dir)
    assert loader.base_path == Path(temp_dir)
    assert loader.base_path.exists()

def test_verify_checksum_missing_file(temp_dir):
    """Test checksum verification on a missing file raises error."""
    loader = DataLoader(base_path=temp_dir)
    with pytest.raises(FileNotFoundError):
        loader.verify_checksum(str(Path(temp_dir) / "missing.txt"))

def test_verify_checksum_no_expected_hash(temp_dir):
    """Test checksum verification passes when no expected hash is provided."""
    # Create a dummy file
    test_file = Path(temp_dir) / "dummy.txt"
    test_file.write_text("test content")
    
    loader = DataLoader(base_path=temp_dir)
    assert loader.verify_checksum(str(test_file)) is True

def test_verify_checksum_match(temp_dir):
    """Test checksum verification with matching hash."""
    test_file = Path(temp_dir) / "dummy.txt"
    test_file.write_text("test content")
    
    loader = DataLoader(base_path=temp_dir)
    # MD5 of "test content"
    expected_md5 = "9473fdd0d880a43c21b7778d34872157"
    assert loader.verify_checksum(str(test_file), expected_md5) is True

def test_verify_checksum_mismatch(temp_dir):
    """Test checksum verification fails with mismatched hash."""
    test_file = Path(temp_dir) / "dummy.txt"
    test_file.write_text("test content")
    
    loader = DataLoader(base_path=temp_dir)
    assert loader.verify_checksum(str(test_file), "wrong_hash") is False

@patch('code.data.download.load_dataset')
@patch('code.data.download.logger')
def test_fetch_dataset_unknown_source(mock_logger, mock_load, temp_dir):
    """Test fetching from an unknown source raises RuntimeError."""
    loader = DataLoader(base_path=temp_dir)
    
    with pytest.raises(RuntimeError) as excinfo:
        loader.fetch_dataset("unknown_source")
    
    assert "Unknown dataset source" in str(excinfo.value)

@patch('code.data.download.load_dataset')
@patch('code.data.download.logger')
def test_fetch_dataset_placeholder_id_raises_error(mock_logger, mock_load, temp_dir):
    """Test that fetch_dataset raises error if placeholder dataset ID is used."""
    loader = DataLoader(base_path=temp_dir)
    
    with pytest.raises(RuntimeError) as excinfo:
        loader.fetch_dataset("huggingface-nist-permeability")
    
    assert "No verified dataset ID provided" in str(excinfo.value)