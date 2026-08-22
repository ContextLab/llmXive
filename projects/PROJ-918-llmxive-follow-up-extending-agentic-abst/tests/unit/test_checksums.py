"""
Unit tests for the checksum management module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Adjust import to match project structure
# Assuming tests are run from root: python -m pytest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.checksums import (
    calculate_file_hash,
    generate_checksums,
    save_checksums,
    load_checksums,
    verify_checksums,
    DATA_DIR
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking data/."""
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()
    
    # Create test files
    file1 = raw_dir / "test1.txt"
    file1.write_text("Hello, World!")
    
    file2 = processed_dir / "test2.txt"
    file2.write_text("Processed data")
    
    return tmp_path

def test_calculate_file_hash(temp_data_dir):
    """Test hash calculation for a known file."""
    file_path = temp_data_dir / "raw" / "test1.txt"
    hash_val = calculate_file_hash(file_path)
    assert len(hash_val) == 64  # SHA-256 hex length
    assert isinstance(hash_val, str)

def test_generate_checksums(temp_data_dir):
    """Test recursive checksum generation."""
    # Temporarily override DATA_DIR for the test
    import data.checksums
    original_dir = data.checksums.DATA_DIR
    data.checksums.DATA_DIR = temp_data_dir
    
    try:
        checksums = generate_checksums(temp_data_dir)
        assert len(checksums) == 2
        assert "raw/test1.txt" in checksums
        assert "processed/test2.txt" in checksums
    finally:
        data.checksums.DATA_DIR = original_dir

def test_save_and_load_checksums(temp_data_dir):
    """Test saving and loading checksums to/from JSON."""
    import data.checksums
    original_dir = data.checksums.DATA_DIR
    data.checksums.DATA_DIR = temp_data_dir
    
    try:
        checksums = generate_checksums(temp_data_dir)
        output_path = temp_data_dir / "checksums.json"
        save_checksums(checksums, output_path)
        
        loaded = load_checksums(output_path)
        assert loaded == checksums
    finally:
        data.checksums.DATA_DIR = original_dir

def test_verify_checksums_success(temp_data_dir):
    """Test successful verification."""
    import data.checksums
    original_dir = data.checksums.DATA_DIR
    data.checksums.DATA_DIR = temp_data_dir
    
    try:
        checksums = generate_checksums(temp_data_dir)
        is_valid, failed = verify_checksums(checksums)
        assert is_valid
        assert len(failed) == 0
    finally:
        data.checksums.DATA_DIR = original_dir

def test_verify_checksums_failure(temp_data_dir):
    """Test verification failure when file is modified."""
    import data.checksums
    original_dir = data.checksums.DATA_DIR
    data.checksums.DATA_DIR = temp_data_dir
    
    try:
        checksums = generate_checksums(temp_data_dir)
        
        # Modify a file
        file_path = temp_data_dir / "raw" / "test1.txt"
        file_path.write_text("Modified content")
        
        is_valid, failed = verify_checksums(checksums)
        assert not is_valid
        assert len(failed) == 1
        assert "raw/test1.txt" in failed[0]
    finally:
        data.checksums.DATA_DIR = original_dir