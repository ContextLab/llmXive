"""
Tests for checksum utilities and directory setup.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

# Import functions from config
from config import (
    ensure_dirs,
    compute_file_checksum,
    compute_directory_checksum,
    save_checksums,
    load_checksums,
    verify_checksums,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    DATA_LOGS_DIR
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_ensure_dirs_creates_directories():
    """Test that ensure_dirs creates all required directories."""
    # Note: In real usage, this creates dirs in the project root
    # For testing, we just verify the function runs without error
    dirs = ensure_dirs()
    for d in dirs:
        assert d.exists(), f"Directory {d} was not created"
        assert d.is_dir(), f"{d} is not a directory"
        # Check for .gitkeep
        gitkeep = d / ".gitkeep"
        assert gitkeep.exists(), f".gitkeep not created in {d}"

def test_compute_file_checksum():
    """Test file checksum computation."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)

    try:
        checksum = compute_file_checksum(temp_path)
        assert len(checksum) == 64, "SHA-256 checksum should be 64 hex characters"
        
        # Verify against known value
        expected = hashlib.sha256(b"test content").hexdigest()
        assert checksum == expected, f"Checksum mismatch: {checksum} != {expected}"
    finally:
        temp_path.unlink()

def test_compute_directory_checksum(temp_dir):
    """Test directory checksum computation."""
    # Create test files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.txt").write_text("content2")
    (temp_dir / ".gitkeep").write_text("gitkeep content")  # Should be excluded

    checksums = compute_directory_checksum(temp_dir)
    
    # Should have 2 files (excluding .gitkeep)
    assert len(checksums) == 2, f"Expected 2 files, got {len(checksums)}"
    
    # Check that files are sorted
    files = [item[0] for item in checksums]
    assert files == sorted(files), "Files should be sorted"

def test_save_and_load_checksums(temp_dir):
    """Test saving and loading checksums."""
    checksums = [
        ("file1.txt", "abc123"),
        ("file2.txt", "def456")
    ]
    output_path = temp_dir / "checksums.json"
    
    save_checksums(checksums, output_path)
    assert output_path.exists(), "Checksum file was not created"
    
    loaded = load_checksums(output_path)
    assert len(loaded) == len(checksums), "Number of checksums mismatch"
    assert loaded == checksums, "Checksums content mismatch"

def test_verify_checksums_success(temp_dir):
    """Test successful checksum verification."""
    # Create files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.txt").write_text("content2")
    
    # Generate real checksums
    actual_checksums = compute_directory_checksum(temp_dir)
    checksum_file = temp_dir / "checksums.json"
    save_checksums(actual_checksums, checksum_file)
    
    # Verify
    assert verify_checksums(temp_dir, checksum_file), "Verification should succeed"

def test_verify_checksums_failure(temp_dir):
    """Test failed checksum verification."""
    # Create files
    (temp_dir / "file1.txt").write_text("content1")
    
    # Create checksums with wrong values
    fake_checksums = [("file1.txt", "wronghash123")]
    checksum_file = temp_dir / "checksums.json"
    save_checksums(fake_checksums, checksum_file)
    
    # Verify should fail
    assert not verify_checksums(temp_dir, checksum_file), "Verification should fail"

def test_gitkeep_files_exist():
    """Test that .gitkeep files exist in data directories."""
    # This test assumes ensure_dirs has been run
    # In CI, this would be part of the setup
    data_dirs = [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_LOGS_DIR]
    for d in data_dirs:
        if d.exists():
            gitkeep = d / ".gitkeep"
            assert gitkeep.exists(), f".gitkeep missing in {d}"
