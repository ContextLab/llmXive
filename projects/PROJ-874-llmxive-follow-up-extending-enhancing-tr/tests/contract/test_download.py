"""
Contract tests for data download functionality.
Verifies that download.py correctly fetches and validates datasets.
"""
import os
import sys
import pytest
from pathlib import Path
import json
import hashlib

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.download import (
    calculate_file_hash,
    verify_checksums,
    DATASET_CONFIGS,
    DATA_ROOT
)

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    return test_dir

def test_calculate_file_hash(temp_dir):
    """Test file hash calculation."""
    test_file = temp_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    calculated_hash = calculate_file_hash(test_file)
    
    # SHA256 of "Hello, World!"
    expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert calculated_hash == expected_hash

def test_verify_checksums_success(temp_dir):
    """Test checksum verification with valid files."""
    # Create test files
    file1 = temp_dir / "file1.txt"
    file1.write_text("content1")
    
    file2 = temp_dir / "file2.txt"
    file2.write_text("content2")
    
    # Create checksums
    checksums = {
        "file1.txt": calculate_file_hash(file1),
        "file2.txt": calculate_file_hash(file2)
    }
    
    checksums_file = temp_dir / "checksums.json"
    with open(checksums_file, "w") as f:
        json.dump(checksums, f)
    
    success, failed = verify_checksums("test", temp_dir, checksums_file)
    
    assert success is True
    assert len(failed) == 0

def test_verify_checksums_missing_file(temp_dir):
    """Test checksum verification with missing file."""
    # Create checksums for non-existent file
    checksums = {
        "missing.txt": "somehash"
    }
    
    checksums_file = temp_dir / "checksums.json"
    with open(checksums_file, "w") as f:
        json.dump(checksums, f)
    
    success, failed = verify_checksums("test", temp_dir, checksums_file)
    
    assert success is False
    assert "missing.txt" in failed

def test_verify_checksums_checksum_mismatch(temp_dir):
    """Test checksum verification with mismatched hash."""
    # Create test file
    test_file = temp_dir / "test.txt"
    test_file.write_text("content")
    
    # Create checksums with wrong hash
    checksums = {
        "test.txt": "wronghash123"
    }
    
    checksums_file = temp_dir / "checksums.json"
    with open(checksums_file, "w") as f:
        json.dump(checksums, f)
    
    success, failed = verify_checksums("test", temp_dir, checksums_file)
    
    assert success is False
    assert "test.txt" in failed

def test_dataset_configs_exist():
    """Test that all expected datasets are configured."""
    assert "narrlv" in DATASET_CONFIGS
    assert "vbench" in DATASET_CONFIGS
    
    # Check required fields
    for name, config in DATASET_CONFIGS.items():
        assert "repo_id" in config
        assert "split" in config
        assert "description" in config

def test_data_root_exists():
    """Test that DATA_ROOT is correctly set."""
    assert DATA_ROOT == Path("data/raw")
    assert DATA_ROOT.is_absolute() == False  # Should be relative
    assert len(DATA_ROOT.parts) == 2  # data, raw
