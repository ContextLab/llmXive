import json
import tempfile
from pathlib import Path
import pytest

from code.data.checksum import (
    compute_sha256,
    generate_checksums,
    save_checksums,
    load_checksums,
    verify_checksums,
)
from code.config import DATA_DIR


def test_compute_sha256():
    """Test SHA256 computation on a known string."""
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = compute_sha256(temp_path)
        # Known SHA256 for "test content"
        expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        assert checksum == expected
    finally:
        Path(temp_path).unlink()


def test_generate_checksums(tmp_path):
    """Test checksum generation for multiple files."""
    # Create test files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("content1")
    file2.write_text("content2")
    
    checksums = generate_checksums(tmp_path)
    
    assert len(checksums) == 2
    assert "file1.txt" in checksums
    assert "file2.txt" in checksums
    assert checksums["file1.txt"] != checksums["file2.txt"]


def test_save_and_load_checksums(tmp_path):
    """Test saving and loading checksums to/from JSON."""
    test_checksums = {
        "file1.txt": "abc123",
        "file2.txt": "def456"
    }
    
    output_path = tmp_path / "checksums.json"
    save_checksums(test_checksums, output_path)
    
    assert output_path.exists()
    
    loaded_checksums = load_checksums(output_path)
    assert loaded_checksums == test_checksums


def test_verify_checksums_success(tmp_path):
    """Test successful checksum verification."""
    # Create test files
    file1 = tmp_path / "file1.txt"
    file1.write_text("content1")
    
    # Generate and save checksums
    checksums = generate_checksums(tmp_path)
    output_path = tmp_path / "checksums.json"
    save_checksums(checksums, output_path)
    
    # Verify
    results = verify_checksums(tmp_path, output_path)
    assert results["file1.txt"] is True


def test_verify_checksums_failure(tmp_path):
    """Test checksum verification failure when file is modified."""
    # Create test file
    file1 = tmp_path / "file1.txt"
    file1.write_text("content1")
    
    # Generate and save checksums
    checksums = generate_checksums(tmp_path)
    output_path = tmp_path / "checksums.json"
    save_checksums(checksums, output_path)
    
    # Modify file
    file1.write_text("modified content")
    
    # Verify - should fail
    results = verify_checksums(tmp_path, output_path)
    assert results["file1.txt"] is False


def test_load_checksums_file_not_found():
    """Test loading checksums from non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_checksums(Path("/nonexistent/path/checksums.json"))
