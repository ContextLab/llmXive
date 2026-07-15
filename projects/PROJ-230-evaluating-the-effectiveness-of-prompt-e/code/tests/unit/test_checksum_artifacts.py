import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils.checksum_artifacts import compute_sha256, scan_directory, write_checksums

@pytest.fixture
def temp_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        # Create subdirectories
        (base / "subdir").mkdir()
        # Create test files
        (base / "file1.txt").write_text("Hello, World!")
        (base / "subdir" / "file2.txt").write_text("Test content")
        # Create a hidden file that should be skipped
        (base / ".hidden").write_text("Hidden")
        yield base

def test_compute_sha256(temp_dir):
    """Test SHA-256 computation for a known string."""
    file_path = temp_dir / "file1.txt"
    computed_hash = compute_sha256(file_path)
    
    # Expected hash for "Hello, World!"
    expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
    assert computed_hash == expected_hash
    assert len(computed_hash) == 64

def test_scan_directory(temp_dir):
    """Test directory scanning excludes hidden files."""
    files = scan_directory(temp_dir)
    file_names = [f.name for f in files]
    
    assert "file1.txt" in file_names
    assert "file2.txt" in file_names
    assert ".hidden" not in file_names
    assert len(files) == 2

def test_write_checksums(temp_dir):
    """Test writing checksums to JSON file."""
    output_path = temp_dir / "checksums.json"
    test_checksums = [
        {"file_path": "test.txt", "sha256": "abc123", "size_bytes": 100}
    ]
    
    write_checksums(test_checksums, output_path)
    
    assert output_path.exists()
    with open(output_path, "r") as f:
        data = json.load(f)
    
    assert "generated_at" in data
    assert "checksums" in data
    assert len(data["checksums"]) == 1
    assert data["checksums"][0]["sha256"] == "abc123"

def test_scan_directory_not_found():
    """Test that scanning a non-existent directory raises an error."""
    with pytest.raises(FileNotFoundError):
        scan_directory(Path("/nonexistent/path"))

def test_scan_directory_is_file(temp_dir):
    """Test that scanning a file instead of directory raises an error."""
    file_path = temp_dir / "file1.txt"
    with pytest.raises(NotADirectoryError):
        scan_directory(file_path)
