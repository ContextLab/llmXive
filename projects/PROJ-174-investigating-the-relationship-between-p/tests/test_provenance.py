"""
Unit tests for provenance utilities (T007).

Verifies that:
1. hash_file computes a correct hash for a known file.
2. write_meta creates a JSON file with correct keys (hash, timestamp, source).
3. generate_provenance_for_dataset integrates correctly.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys_path = str(project_root)
if sys_path not in __import__('sys').path:
    __import__('sys').path.insert(0, sys_path)

from utils.provenance import hash_file, write_meta, generate_provenance_for_dataset

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path, ignore_errors=True)

def test_hash_file_valid(temp_dir):
    """Test hash_file on a valid file."""
    test_file = Path(temp_dir) / "test.txt"
    content = b"Hello, provenance!"
    test_file.write_bytes(content)
    
    h = hash_file(str(test_file))
    assert len(h) == 64  # SHA256 hex length
    assert h.isalnum()

def test_hash_file_missing():
    """Test hash_file raises on missing file."""
    with pytest.raises(FileNotFoundError):
        hash_file("/nonexistent/path/file.txt")

def test_write_meta_creates_json(temp_dir):
    """Test write_meta creates a JSON file with required keys."""
    test_file = Path(temp_dir) / "data.csv"
    test_file.write_text("col1,col2\n1,2")
    
    meta_dict = {"custom_key": "custom_value"}
    source = "test_source"
    
    meta_path = write_meta(str(test_file), meta_dict, source=source)
    
    # The function modifies meta_dict in place and returns None, 
    # but the file is written to {path}_meta.json
    expected_meta_path = str(test_file.parent / "data_meta.json")
    
    assert os.path.exists(expected_meta_path)
    
    with open(expected_meta_path, "r") as f:
        data = json.load(f)
    
    assert "hash" in data
    assert "timestamp" in data
    assert "source" in data
    assert data["source"] == source
    assert data["custom_key"] == "custom_value"

def test_write_meta_missing_file():
    """Test write_meta raises on missing source file."""
    with pytest.raises(FileNotFoundError):
        write_meta("/nonexistent/data.csv", {})

def test_generate_provenance_for_dataset(temp_dir):
    """Test the convenience function."""
    test_file = Path(temp_dir) / "dataset.parquet"
    test_file.write_text("fake parquet content")
    
    result_path = generate_provenance_for_dataset(str(test_file), "ds004287")
    
    expected_meta = str(test_file.parent / "dataset_meta.json")
    assert result_path == expected_meta
    assert os.path.exists(expected_meta)
    
    with open(expected_meta, "r") as f:
        data = json.load(f)
    
    assert data["source"] == "ds004287"
    assert "hash" in data
    assert "timestamp" in data
    assert data["dataset_id"] == "dataset.parquet"

def test_write_meta_generates_hash_if_missing(temp_dir):
    """Test that write_meta computes hash if not provided."""
    test_file = Path(temp_dir) / "test.csv"
    test_file.write_text("a,b")
    
    meta_dict = {}  # No hash provided
    write_meta(str(test_file), meta_dict, source="src")
    
    meta_path = str(test_file.parent / "test_meta.json")
    with open(meta_path, "r") as f:
        data = json.load(f)
    
    # Should match the file hash
    assert data["hash"] == hash_file(str(test_file))
