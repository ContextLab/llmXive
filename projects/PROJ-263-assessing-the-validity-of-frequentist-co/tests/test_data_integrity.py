import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

# Mock the config module to avoid dependency on actual project structure during unit tests
import sys
from unittest.mock import patch, MagicMock

# Create a temporary directory for test data
@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "raw"
        processed_dir = Path(tmpdir) / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()
        
        # Mock the config functions
        with patch('data_integrity.get_raw_data_dir', return_value=raw_dir), \
             patch('data_integrity.get_processed_data_dir', return_value=processed_dir):
            yield raw_dir, processed_dir

def test_compute_file_sha256(temp_data_dir):
    """Test SHA-256 computation on a known file."""
    raw_dir, _ = temp_data_dir
    test_file = raw_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)

    # Calculate expected hash manually
    expected_hash = hashlib.sha256(test_content).hexdigest()

    from code.data_integrity import compute_file_sha256
    actual_hash = compute_file_sha256(test_file)

    assert actual_hash == expected_hash

def test_compute_file_sha256_missing_file(temp_data_dir):
    """Test that FileNotFoundError is raised for missing files."""
    raw_dir, _ = temp_data_dir
    missing_file = raw_dir / "nonexistent.txt"

    from code.data_integrity import compute_file_sha256
    with pytest.raises(FileNotFoundError):
        compute_file_sha256(missing_file)

def test_generate_checksums_for_raw_data(temp_data_dir):
    """Test checksum generation for multiple files."""
    raw_dir, _ = temp_data_dir
    
    # Create test files
    file1 = raw_dir / "data1.csv"
    file1.write_text("col1,col2\n1,2")
    
    file2 = raw_dir / "data2.csv"
    file2.write_text("col1,col2\n3,4")

    # Create a hidden file that should be skipped
    hidden_file = raw_dir / ".hidden"
    hidden_file.write_text("secret")

    from code.data_integrity import generate_checksums_for_raw_data
    checksums = generate_checksums_for_raw_data()

    # Check that we have checksums for the two visible files
    assert len(checksums) == 2
    assert str(file1) in checksums
    assert str(file2) in checksums
    assert ".hidden" not in str(checksums)

def test_save_checksums(temp_data_dir):
    """Test saving checksums to a JSON file."""
    raw_dir, processed_dir = temp_data_dir
    
    test_checksums = {
        "file1.csv": "abc123",
        "file2.csv": "def456"
    }

    from code.data_integrity import save_checksums
    output_path = save_checksums(test_checksums)

    assert output_path.exists()
    assert output_path.parent == processed_dir
    
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data == test_checksums

def test_verify_checksums_success(temp_data_dir):
    """Test successful verification of checksums."""
    raw_dir, processed_dir = temp_data_dir
    
    # Create a test file
    test_file = raw_dir / "verify_test.csv"
    test_content = b"verification test"
    test_file.write_bytes(test_content)
    expected_hash = hashlib.sha256(test_content).hexdigest()
    
    # Create checksums file
    checksums = {str(test_file): expected_hash}
    checksums_path = processed_dir / "checksums.json"
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f)

    from code.data_integrity import verify_checksums
    assert verify_checksums(checksums_path) is True

def test_verify_checksums_mismatch(temp_data_dir):
    """Test verification failure when checksums don't match."""
    raw_dir, processed_dir = temp_data_dir
    
    # Create a test file
    test_file = raw_dir / "mismatch_test.csv"
    test_content = b"original content"
    test_file.write_bytes(test_content)
    
    # Create checksums file with wrong hash
    wrong_hash = hashlib.sha256(b"different content").hexdigest()
    checksums = {str(test_file): wrong_hash}
    checksums_path = processed_dir / "checksums.json"
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f)

    from code.data_integrity import verify_checksums
    assert verify_checksums(checksums_path) is False

def test_verify_checksums_missing_file(temp_data_dir):
    """Test verification failure when a file is missing."""
    raw_dir, processed_dir = temp_data_dir
    
    # Create checksums file referencing a non-existent file
    checksums = {str(raw_dir / "missing.csv"): "somehash"}
    checksums_path = processed_dir / "checksums.json"
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f)

    from code.data_integrity import verify_checksums
    assert verify_checksums(checksums_path) is False

def test_main_function(temp_data_dir):
    """Test the main function execution."""
    raw_dir, processed_dir = temp_data_dir
    
    # Create a test file
    test_file = raw_dir / "main_test.csv"
    test_file.write_text("test,data\n1,2")

    from code.data_integrity import main
    # This should run without raising exceptions
    main()
    
    # Verify that checksums file was created
    checksums_path = processed_dir / "checksums.json"
    assert checksums_path.exists()
    
    with open(checksums_path, 'r') as f:
        checksums = json.load(f)
    
    assert len(checksums) >= 1
