"""
Unit tests for code/utils/hash_artifacts.py
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from code.utils.hash_artifacts import (
    compute_sha256,
    find_artifacts,
    hash_directory,
    hash_multiple_dirs,
    verify_checksums,
    EXCLUDED_FILES
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create test files
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "sample.csv").write_text("a,b,c\n1,2,3")
        (tmp_path / "data" / "sample.json").write_text('{"key": "value"}')
        (tmp_path / "data" / "skip.txt").write_text("should be skipped if extension not in list")
        
        # Create a nested directory
        (tmp_path / "data" / "nested").mkdir()
        (tmp_path / "data" / "nested" / "deep.json").write_text('{"nested": true}')
        
        # Create excluded file
        (tmp_path / "data" / ".gitkeep").write_text("excluded")
        
        yield tmp_path


def test_compute_sha256(temp_dir):
    """Test SHA-256 computation on a known file."""
    file_path = temp_dir / "data" / "sample.csv"
    hash1 = compute_sha256(file_path)
    hash2 = compute_sha256(file_path)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length
    assert hash1.isalnum()


def test_compute_sha256_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("nonexistent_file.txt"))


def test_find_artifacts(temp_dir):
    """Test artifact discovery with extension filtering."""
    artifacts = find_artifacts(temp_dir / "data")
    names = [p.name for p in artifacts]
    
    assert "sample.csv" in names
    assert "sample.json" in names
    assert "deep.json" in names
    assert ".gitkeep" not in names  # Excluded
    assert "skip.txt" in names  # .txt is in default extensions


def test_find_artifacts_custom_extensions(temp_dir):
    """Test artifact discovery with custom extension filter."""
    artifacts = find_artifacts(
        temp_dir / "data", 
        extensions={".json"}
    )
    names = [p.name for p in artifacts]
    
    assert "sample.json" in names
    assert "deep.json" in names
    assert "sample.csv" not in names
    assert "skip.txt" not in names


def test_hash_directory(temp_dir):
    """Test hashing a directory and saving results."""
    output_file = temp_dir / "checksums.json"
    results = hash_directory(temp_dir / "data", output_file)
    
    assert len(results) > 0
    assert output_file.exists()
    
    # Verify JSON structure
    with open(output_file, "r") as f:
        data = json.load(f)
    
    assert "sample.csv" in data
    assert "sample.json" in data
    assert data["sample.csv"] == results["sample.csv"]


def test_hash_directory_missing_dir():
    """Test hashing a non-existent directory returns empty dict."""
    results = hash_directory(Path("nonexistent_dir"))
    assert results == {}


def test_hash_multiple_dirs(temp_dir):
    """Test hashing multiple directories."""
    # Create a second directory
    (temp_dir / "docs").mkdir()
    (temp_dir / "docs" / "report.json").write_text('{"report": true}')
    
    results = hash_multiple_dirs(
        [str(temp_dir / "data"), str(temp_dir / "docs")],
        output_dir=temp_dir
    )
    
    assert "data" in results
    assert "docs" in results
    assert "sample.csv" in results["data"]
    assert "report.json" in results["docs"]


def test_verify_checksums(temp_dir):
    """Test verification of valid checksums."""
    # Create checksums first
    checksum_file = temp_dir / "checksums.json"
    hash_directory(temp_dir / "data", checksum_file)
    
    # Verify should pass
    assert verify_checksums(checksum_file) is True


def test_verify_checksums_modified_file(temp_dir):
    """Test verification fails when file is modified."""
    checksum_file = temp_dir / "checksums.json"
    hash_directory(temp_dir / "data", checksum_file)
    
    # Modify a file
    csv_file = temp_dir / "data" / "sample.csv"
    original_content = csv_file.read_text()
    csv_file.write_text(original_content + "\nmodified")
    
    assert verify_checksums(checksum_file) is False
    
    # Restore content
    csv_file.write_text(original_content)


def test_verify_checksums_missing_file(temp_dir):
    """Test verification fails when file is missing."""
    checksum_file = temp_dir / "checksums.json"
    hash_directory(temp_dir / "data", checksum_file)
    
    # Remove a file
    csv_file = temp_dir / "data" / "sample.csv"
    csv_file.unlink()
    
    assert verify_checksums(checksum_file) is False

def test_main_function(capsys, temp_dir):
    """Test the main function execution."""
    import sys
    
    # Test default behavior (no args)
    sys.argv = ["hash_artifacts.py"]
    # Mock the default dirs to use our temp dir to avoid cluttering
    # For this test, we just ensure it runs without error
    # We can't easily test the default behavior without mocking DEFAULT_SCAN_DIRS
    # So we test with explicit args instead
    
    # Test with explicit directory
    sys.argv = ["hash_artifacts.py", str(temp_dir / "data")]
    from code.utils.hash_artifacts import main
    main()
    
    captured = capsys.readouterr()
    assert "Hashing directory" in captured.out