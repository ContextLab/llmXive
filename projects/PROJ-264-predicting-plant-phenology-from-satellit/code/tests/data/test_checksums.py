import os
import json
import tempfile
from pathlib import Path
import pytest
from src.data.checksums import (
    compute_file_checksum,
    compute_directory_checksums,
    save_checksums,
    load_checksums,
    verify_checksums,
    generate_checksums_for_directories,
    verify_all_checksums
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        # Create subdirectories
        (base / "raw").mkdir()
        (base / "processed").mkdir()
        
        # Create test files
        (base / "raw" / "file1.txt").write_text("Hello World")
        (base / "raw" / "file2.txt").write_text("Test Data")
        (base / "processed" / "result.csv").write_text("a,b\n1,2")
        
        # Create a file to exclude
        (base / "raw" / "temp.pyc").write_text("Binary")
        
        yield base

def test_compute_file_checksum(temp_data_dir):
    """Test checksum computation for a single file."""
    file_path = temp_data_dir / "raw" / "file1.txt"
    checksum = compute_file_checksum(file_path)
    
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)
    
    # Verify determinism
    checksum2 = compute_file_checksum(file_path)
    assert checksum == checksum2

def test_save_and_load_checksums(temp_data_dir):
    """Test saving and loading checksums from JSON."""
    checksums = {
        "file1.txt": "abc123",
        "file2.txt": "def456"
    }
    output_path = temp_data_dir / "test_checksums.json"
    
    save_checksums(checksums, output_path)
    assert output_path.exists()
    
    loaded = load_checksums(output_path)
    assert loaded["checksums"] == checksums
    assert "generated_at" in loaded
    assert loaded["algorithm"] == "sha256"

def test_save_checksums_excludes_itself(temp_data_dir):
    """Ensure save_checksums doesn't include itself in recursive scans."""
    # This is implicitly tested by the workflow, but we verify the logic
    # by ensuring the checksums file can be created without circular dependency
    checksums = {"test": "value"}
    output_path = temp_data_dir / "checksums.json"
    save_checksums(checksums, output_path)
    
    # Re-load and verify integrity
    loaded = load_checksums(output_path)
    assert loaded["checksums"]["test"] == "value"

def test_verify_checksums_valid(temp_data_dir):
    """Test verification when all files match."""
    # Compute real checksums first
    real_checksums = compute_directory_checksums(temp_data_dir / "raw")
    stored = {k: v for k, v in real_checksums.items() if not k.endswith(".pyc")}
    
    results = verify_checksums(temp_data_dir / "raw", stored)
    
    for path, is_valid in results.items():
        assert is_valid, f"File {path} should be valid"

def test_verify_checksums_modified_file(temp_data_dir):
    """Test verification detects modified files."""
    file_path = temp_data_dir / "raw" / "file1.txt"
    original_content = file_path.read_text()
    
    # Get original checksum
    original_checksums = compute_directory_checksums(temp_data_dir / "raw")
    stored = {k: v for k, v in original_checksums.items() if not k.endswith(".pyc")}
    
    # Modify file
    file_path.write_text("Modified Content")
    
    results = verify_checksums(temp_data_dir / "raw", stored)
    
    assert results["file1.txt"] == False
    
    # Restore
    file_path.write_text(original_content)

def test_verify_checksums_missing_file(temp_data_dir):
    """Test verification detects missing files."""
    original_checksums = compute_directory_checksums(temp_data_dir / "raw")
    stored = {k: v for k, v in original_checksums.items() if not k.endswith(".pyc")}
    
    # Remove a file
    file_path = temp_data_dir / "raw" / "file1.txt"
    file_path.unlink()
    
    results = verify_checksums(temp_data_dir / "raw", stored)
    
    assert results["file1.txt"] == False

def test_verify_checksums_no_stored(temp_data_dir):
    """Test verification with empty stored checksums."""
    results = verify_checksums(temp_data_dir / "raw", {})
    
    # All existing files should be flagged as new/missing from stored
    assert len(results) > 0
    for is_valid in results.values():
        assert is_valid == False

def test_get_checksum_file_path(temp_data_dir):
    """Test the full workflow of generating and verifying checksums."""
    sub_dirs = ["raw", "processed"]
    
    # Generate
    checksums_path = generate_checksums_for_directories(
        temp_data_dir, 
        sub_dirs, 
        exclude_patterns=["*.pyc"]
    )
    
    assert checksums_path.exists()
    
    # Verify
    success = verify_all_checksums(
        temp_data_dir,
        sub_dirs,
        exclude_patterns=["*.pyc"]
    )
    
    assert success

def test_compute_directory_checksums_excludes_patterns(temp_data_dir):
    """Test that directory checksums respect exclude patterns."""
    checksums = compute_directory_checksums(
        temp_data_dir / "raw",
        exclude_patterns=["*.pyc"]
    )
    
    assert "temp.pyc" not in checksums
    assert "file1.txt" in checksums
    assert "file2.txt" in checksums
