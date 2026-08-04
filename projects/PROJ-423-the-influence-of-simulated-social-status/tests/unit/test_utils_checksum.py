import os
import json
import tempfile
import pytest
from code.utils import calculate_checksum, append_checksum_to_file

def test_calculate_checksum():
    """Test that calculate_checksum returns a valid SHA256 hex string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = calculate_checksum(temp_path)
        assert len(checksum) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
    finally:
        os.unlink(temp_path)

def test_append_checksum_to_file():
    """Test that append_checksum_to_file correctly updates the checksums JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy file to checksum
        dummy_file = os.path.join(tmpdir, "dummy.txt")
        with open(dummy_file, 'w') as f:
            f.write("dummy data")
        
        # Create checksums file path
        checksums_file = os.path.join(tmpdir, "checksums.json")
        
        # Run the function
        append_checksum_to_file(dummy_file, checksums_file)
        
        # Verify the file was created and contains the correct data
        assert os.path.exists(checksums_file)
        with open(checksums_file, 'r') as f:
            data = json.load(f)
        
        assert "files" in data
        assert dummy_file in data["files"]
        
        # Verify the checksum matches the direct calculation
        expected_checksum = calculate_checksum(dummy_file)
        assert data["files"][dummy_file] == expected_checksum

def test_append_checksum_to_file_missing_input():
    """Test that append_checksum_to_file raises FileNotFoundError for missing input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent = os.path.join(tmpdir, "nope.txt")
        checksums_file = os.path.join(tmpdir, "checksums.json")
        
        with pytest.raises(FileNotFoundError):
            append_checksum_to_file(non_existent, checksums_file)

def test_append_checksum_to_file_creates_checksums_file():
    """Test that append_checksum_to_file creates the checksums file if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_file = os.path.join(tmpdir, "dummy.txt")
        with open(dummy_file, 'w') as f:
            f.write("data")
        
        checksums_file = os.path.join(tmpdir, "new_checksums.json")
        assert not os.path.exists(checksums_file)
        
        append_checksum_to_file(dummy_file, checksums_file)
        
        assert os.path.exists(checksums_file)
        with open(checksums_file, 'r') as f:
            data = json.load(f)
        assert len(data["files"]) == 1
