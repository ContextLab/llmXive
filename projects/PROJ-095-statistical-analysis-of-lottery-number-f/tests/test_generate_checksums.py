"""
Unit tests for the checksum generation functionality (T008b).
"""
import json
import os
import tempfile
import hashlib
import pytest
from pathlib import Path

# Import the function to test (we'll test the logic directly or via the script)
# Since main() is the entry point, we'll test the underlying logic
import sys
from code.data_utils import calculate_checksum, save_checksums_file, load_checksums_file
from code.exceptions import LotteryDataError

def test_calculate_checksum():
    """Test that calculate_checksum returns a valid SHA256 hash."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("test,data\n1,2\n")
        temp_path = f.name
    
    try:
        checksum = calculate_checksum(temp_path)
        
        # Verify it's a valid hex string of correct length (64 chars for SHA256)
        assert isinstance(checksum, str)
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)
        
        # Verify against manual calculation
        with open(temp_path, 'rb') as f:
            expected = hashlib.sha256(f.read()).hexdigest()
        
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_save_and_load_checksums_file():
    """Test saving and loading checksums to/from JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.csv")
        output_file = os.path.join(tmpdir, "checksums.json")
        
        # Create a test file
        with open(test_file, 'w') as f:
            f.write("test")
        
        # Calculate and save checksum
        checksum = calculate_checksum(test_file)
        checksums_data = {
            "files": {
                "test.csv": {
                    "sha256": checksum,
                    "size_bytes": 4
                }
            }
        }
        
        save_checksums_file(output_file, checksums_data)
        
        # Verify file exists
        assert os.path.exists(output_file)
        
        # Load and verify
        loaded_data = load_checksums_file(output_file)
        
        assert "files" in loaded_data
        assert "test.csv" in loaded_data["files"]
        assert loaded_data["files"]["test.csv"]["sha256"] == checksum

def test_checksum_for_known_content():
    """Test checksum calculation for known content."""
    test_content = "specific,test,content\n1,2,3\n"
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write(test_content)
        temp_path = f.name
    
    try:
        checksum = calculate_checksum(temp_path)
        
        # Manual calculation
        expected = hashlib.sha256(test_content.encode('utf-8')).hexdigest()
        
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_missing_file_raises_error():
    """Test that calculating checksum for missing file raises error."""
    # Note: calculate_checksum might handle this differently, 
    # but the main script should raise LotteryDataError
    with pytest.raises(FileNotFoundError):
        calculate_checksum("nonexistent_file.csv")
