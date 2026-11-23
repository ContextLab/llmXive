import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from utils import calculate_checksum, append_to_checksums, load_json

@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_checksum_file():
    """Create a temporary checksums file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({"files": {}}, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_calculate_checksum(temp_file):
    """Test that calculate_checksum returns a valid SHA256 hex string."""
    checksum = calculate_checksum(temp_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)

def test_append_to_checksums_creates_file(temp_file, temp_checksum_file):
    """Test that append_to_checksums updates the checksums file correctly."""
    append_to_checksums(temp_file, temp_checksum_file)
    
    loaded = load_json(temp_checksum_file)
    assert "files" in loaded
    assert temp_file in loaded["files"]
    assert loaded["files"][temp_file] == calculate_checksum(temp_file)

def test_append_to_checksums_handles_missing_file():
    """Test that append_to_checksums raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        append_to_checksums("/nonexistent/path/file.txt", "/tmp/checksums.json")

def test_append_to_checksums_initializes_missing_checksums_file(temp_file):
    """Test that append_to_checksums creates checksums file if it doesn't exist."""
    temp_path = tempfile.mktemp(suffix='.json')
    try:
        append_to_checksums(temp_file, temp_path)
        
        assert os.path.exists(temp_path)
        loaded = load_json(temp_path)
        assert "files" in loaded
        assert temp_file in loaded["files"]
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_append_to_checksums_preserves_existing_entries(temp_file, temp_checksum_file):
    """Test that append_to_checksums preserves existing entries."""
    # Add an existing entry
    existing_file = tempfile.mktemp(suffix='.txt')
    with open(existing_file, 'w') as f:
        f.write("Existing content")
    
    with open(temp_checksum_file, 'w') as f:
        json.dump({"files": {existing_file: "fake_checksum"}}, f)
    
    append_to_checksums(temp_file, temp_checksum_file)
    
    loaded = load_json(temp_checksum_file)
    assert existing_file in loaded["files"]
    assert temp_file in loaded["files"]
    assert loaded["files"][existing_file] == "fake_checksum"  # Preserved
    assert loaded["files"][temp_file] == calculate_checksum(temp_file)
    
    # Cleanup
    os.unlink(existing_file)