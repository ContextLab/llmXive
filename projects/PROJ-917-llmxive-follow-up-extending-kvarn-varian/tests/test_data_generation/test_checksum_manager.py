import pytest
import tempfile
from pathlib import Path
import json
import os

from data_checksum_manager import (
    create_directories,
    compute_file_checksum,
    record_checksums,
    save_checksums,
    load_checksums,
    verify_integrity
)

@pytest.fixture
def project_root():
    """Create a temporary project root for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_create_directories_structure(project_root):
    """Test that create_directories creates the expected structure."""
    data_path = create_directories(str(project_root))
    
    expected_dirs = [
        "data/generated",
        "data/models", 
        "data/simulation",
        "data/analysis",
        "data/raw"
    ]
    
    for subdir in expected_dirs:
        dir_path = project_root / subdir
        assert dir_path.exists(), f"Directory {subdir} was not created"
        assert dir_path.is_dir(), f"{subdir} is not a directory"
        
        # Check for .gitkeep
        keep_file = dir_path / ".gitkeep"
        assert keep_file.exists(), f".gitkeep missing in {subdir}"

def test_compute_file_checksum_sha256(project_root):
    """Test checksum computation with SHA256."""
    test_file = project_root / "test.txt"
    test_file.write_text("test content")
    
    checksum = compute_file_checksum(test_file)
    
    # SHA256 produces 64 hex characters
    assert len(checksum) == 64
    assert all(c in '0123456789abcdef' for c in checksum)

def test_compute_file_checksum_not_found(project_root):
    """Test checksum computation on non-existent file."""
    non_existent = project_root / "nonexistent.txt"
    
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(non_existent)

def test_record_checksums_excludes_gitkeep(project_root):
    """Test that .gitkeep files are excluded from checksums."""
    create_directories(str(project_root))
    
    # Create a real file
    real_file = project_root / "data" / "generated" / "real.txt"
    real_file.parent.mkdir(parents=True, exist_ok=True)
    real_file.write_text("real content")
    
    checksums = record_checksums(project_root / "data")
    
    # Should only have the real file, not .gitkeep
    paths = [c["path"] for c in checksums]
    assert any("real.txt" in p for p in paths)
    assert not any(".gitkeep" in p for p in paths)

def test_save_load_checksums_roundtrip(project_root):
    """Test saving and loading checksums preserves data."""
    create_directories(str(project_root))
    
    # Create test file
    test_file = project_root / "data" / "generated" / "test.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("test content")
    
    # Record and save
    original_checksums = record_checksums(project_root / "data")
    output_path = project_root / "data" / "checksums.json"
    save_checksums(original_checksums, output_path)
    
    # Load
    loaded_checksums = load_checksums(output_path)
    
    # Verify structure
    assert len(original_checksums) == len(loaded_checksums)
    for orig, loaded in zip(original_checksums, loaded_checksums):
        assert orig["path"] == loaded["path"]
        assert orig["checksum"] == loaded["checksum"]
        assert orig["algorithm"] == loaded["algorithm"]

def test_verify_integrity_complete(project_root):
    """Test complete integrity verification workflow."""
    create_directories(str(project_root))
    
    # Create test files
    file1 = project_root / "data" / "generated" / "file1.txt"
    file2 = project_root / "data" / "models" / "file2.txt"
    
    file1.parent.mkdir(parents=True, exist_ok=True)
    file2.parent.mkdir(parents=True, exist_ok=True)
    
    file1.write_text("content 1")
    file2.write_text("content 2")
    
    # Record and save
    checksums = record_checksums(project_root / "data")
    output_path = project_root / "data" / "checksums.json"
    save_checksums(checksums, output_path)
    
    # Verify
    results = verify_integrity(project_root / "data", output_path)
    
    assert results["status"] == "success"
    assert results["verified"] == 2
    assert results["failed"] == 0
    assert results["missing"] == 0

def test_verify_integrity_partial_failure(project_root):
    """Test integrity verification with partial failures."""
    create_directories(str(project_root))
    
    # Create test files
    file1 = project_root / "data" / "generated" / "file1.txt"
    file2 = project_root / "data" / "models" / "file2.txt"
    
    file1.parent.mkdir(parents=True, exist_ok=True)
    file2.parent.mkdir(parents=True, exist_ok=True)
    
    file1.write_text("content 1")
    file2.write_text("content 2")
    
    # Record and save
    checksums = record_checksums(project_root / "data")
    output_path = project_root / "data" / "checksums.json"
    save_checksums(checksums, output_path)
    
    # Delete one file
    file2.unlink()
    
    # Verify should show partial failure
    results = verify_integrity(project_root / "data", output_path)
    
    assert results["status"] == "failed"
    assert results["verified"] == 1
    assert results["missing"] == 1
    assert results["failed"] == 0

def test_verify_missing_checksum_file(project_root):
    """Test verification when checksum file is missing."""
    create_directories(str(project_root))
    
    non_existent_checksum = project_root / "data" / "missing.json"
    
    results = verify_integrity(project_root / "data", non_existent_checksum)
    
    assert results["status"] == "error"
    assert "Checksum file not found" in results["message"]