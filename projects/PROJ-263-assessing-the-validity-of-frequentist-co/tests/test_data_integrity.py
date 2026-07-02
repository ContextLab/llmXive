"""
Unit tests for the data_integrity module.
"""
import os
import json
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# We need to mock the config imports if they rely on global state, 
# but for this test we assume standard project structure or mock paths.
import sys
from io import StringIO

# Mock the config module to avoid dependency on full project setup during unit tests
class MockConfig:
    @staticmethod
    def get_data_dir():
        return Path(tempfile.gettempdir()) / "llmXive_test_data"
    
    @staticmethod
    def get_output_dir():
        return Path(tempfile.gettempdir()) / "llmXive_test_output"

# Inject mock before importing data_integrity if necessary, 
# but since we are testing logic that uses Path operations, 
# we will patch the specific functions used.

# We will import the module and patch the config functions directly in the module
import importlib
import data_integrity

@pytest.fixture
def temp_data_structure():
    """Create a temporary directory structure for testing."""
    base = Path(tempfile.gettempdir()) / "llmXive_test_data"
    raw_dir = base / "raw"
    processed_dir = base / "processed"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a test file
    test_file = raw_dir / "test_data.csv"
    test_file.write_text("col1,col2\n1,2\n3,4")
    
    yield {
        "base": base,
        "raw": raw_dir,
        "processed": processed_dir,
        "test_file": test_file
    }
    
    # Cleanup
    import shutil
    shutil.rmtree(base, ignore_errors=True)

def test_compute_file_sha256(temp_data_structure):
    """Test SHA-256 computation on a known file."""
    test_file = temp_data_structure["test_file"]
    
    # Calculate expected hash manually
    expected_hash = hashlib.sha256(test_file.read_bytes()).hexdigest()
    
    # Call function
    result = data_integrity.compute_file_sha256(test_file)
    
    assert result == expected_hash
    assert len(result) == 64  # SHA-256 hex length

def test_generate_checksums_for_raw_data(temp_data_structure):
    """Test the full generation process."""
    # Patch get_data_dir to return our temp dir
    with patch.object(data_integrity, 'get_data_dir', return_value=temp_data_structure["base"]):
        record = data_integrity.generate_checksums_for_raw_data()
    
    assert record["total_files"] == 1
    assert len(record["files"]) == 1
    assert record["files"][0]["filename"] == "test_data.csv"
    assert "checksum" in record["files"][0]
    assert len(record["files"][0]["checksum"]) == 64

def test_save_checksums(temp_data_structure):
    """Test saving checksums to JSON."""
    test_record = {
        "version": "1.0",
        "files": [
            {"filename": "test.csv", "checksum": "abc123"}
        ]
    }
    
    output_path = temp_data_structure["processed"] / "test_checksums.json"
    
    with patch.object(data_integrity, 'get_data_dir', return_value=temp_data_structure["base"]):
        saved_path = data_integrity.save_checksums(test_record, output_path)
    
    assert saved_path.exists()
    with open(saved_path, "r") as f:
        loaded = json.load(f)
    
    assert loaded == test_record

def test_verify_checksums_success(temp_data_structure):
    """Test verification when files match."""
    # Generate real checksums first
    with patch.object(data_integrity, 'get_data_dir', return_value=temp_data_structure["base"]):
        record = data_integrity.generate_checksums_for_raw_data()
        data_integrity.save_checksums(record)
    
    # Verify
    with patch.object(data_integrity, 'get_data_dir', return_value=temp_data_structure["base"]):
        is_valid = data_integrity.verify_checksums()
    
    assert is_valid is True

def test_verify_checksums_failure(temp_data_structure):
    """Test verification when file is modified."""
    # Generate checksums
    with patch.object(data_integrity, 'get_data_dir', return_value=temp_data_structure["base"]):
        record = data_integrity.generate_checksums_for_raw_data()
        data_integrity.save_checksums(record)
    
    # Modify file
    temp_data_structure["test_file"].write_text("modified content")
    
    # Verify should fail
    with patch.object(data_integrity, 'get_data_dir', return_value=temp_data_structure["base"]):
        is_valid = data_integrity.verify_checksums()
    
    assert is_valid is False

def test_missing_file_verification(temp_data_structure):
    """Test verification when a file is deleted."""
    # Generate checksums
    with patch.object(data_integrity, 'get_data_dir', return_value=temp_data_structure["base"]):
        record = data_integrity.generate_checksums_for_raw_data()
        data_integrity.save_checksums(record)
    
    # Delete file
    temp_data_structure["test_file"].unlink()
    
    # Verify should fail
    with patch.object(data_integrity, 'get_data_dir', return_value=temp_data_structure["base"]):
        is_valid = data_integrity.verify_checksums()
    
    assert is_valid is False
