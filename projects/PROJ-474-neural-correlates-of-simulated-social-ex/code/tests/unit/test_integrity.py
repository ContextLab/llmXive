"""
Unit tests for the data integrity checker module.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import hashlib

from src.integrity import (
    compute_file_hash,
    generate_hashes,
    save_hashes,
    load_hashes,
    verify_integrity,
    update_hashes,
    IntegrityError,
    DEFAULT_DATA_DIR,
    DEFAULT_STATE_DIR
)


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        state_dir = Path(tmpdir) / "state"
        data_dir.mkdir()
        state_dir.mkdir()
        yield data_dir, state_dir


@pytest.fixture
def sample_files(temp_dirs):
    """Create sample files in the data directory."""
    data_dir, _ = temp_dirs
    files = {}
    
    # Create a simple text file
    file1 = data_dir / "test1.txt"
    content1 = "Hello, World!"
    file1.write_text(content1)
    files["test1.txt"] = content1
    
    # Create a nested file
    subdir = data_dir / "subdir"
    subdir.mkdir()
    file2 = subdir / "test2.txt"
    content2 = "Nested content"
    file2.write_text(content2)
    files["subdir/test2.txt"] = content2
    
    # Create a binary file
    file3 = data_dir / "binary.bin"
    content3 = b"\x00\x01\x02\x03"
    file3.write_bytes(content3)
    files["binary.bin"] = content3
    
    return files, data_dir


def test_compute_file_hash_sample_files(sample_files):
    """Test hash computation for sample files."""
    files, data_dir = sample_files
    
    for rel_path, content in files.items():
        file_path = data_dir / rel_path
        if isinstance(content, str):
            expected_hash = hashlib.sha256(content.encode()).hexdigest()
        else:
            expected_hash = hashlib.sha256(content).hexdigest()
        
        computed_hash = compute_file_hash(file_path)
        assert computed_hash == expected_hash, f"Hash mismatch for {rel_path}"


def test_compute_file_hash_nonexistent():
    """Test that computing hash of non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash(Path("nonexistent_file.txt"))


def test_generate_hashes(sample_files, temp_dirs):
    """Test hash generation for all files in data directory."""
    files, data_dir = sample_files
    _, state_dir = temp_dirs
    
    hashes = generate_hashes(data_dir)
    
    assert len(hashes) == len(files), "Number of hashes should match number of files"
    
    for rel_path, content in files.items():
        assert rel_path in hashes, f"Missing hash for {rel_path}"
        # Verify the hash is a valid SHA-256 hex string
        assert len(hashes[rel_path]) == 64, "Hash should be 64 characters long"
        assert all(c in '0123456789abcdef' for c in hashes[rel_path]), "Hash should be hex"


def test_save_and_load_hashes(sample_files, temp_dirs):
    """Test saving and loading hashes."""
    files, data_dir = sample_files
    _, state_dir = temp_dirs
    
    # Generate and save hashes
    hashes = generate_hashes(data_dir)
    save_hashes(hashes, state_dir)
    
    # Load hashes back
    loaded_hashes = load_hashes(state_dir)
    
    assert loaded_hashes == hashes, "Loaded hashes should match saved hashes"


def test_load_hashes_no_file(temp_dirs):
    """Test loading hashes when no file exists."""
    _, state_dir = temp_dirs
    
    # Should return empty dict, not raise error
    hashes = load_hashes(state_dir)
    assert hashes == {}, "Should return empty dict when no hash store exists"


def test_verify_integrity_match(sample_files, temp_dirs):
    """Test verification when files match stored hashes."""
    files, data_dir = sample_files
    _, state_dir = temp_dirs
    
    # Generate and save hashes
    hashes = generate_hashes(data_dir)
    save_hashes(hashes, state_dir)
    
    # Verify should pass
    result = verify_integrity(data_dir, state_dir)
    assert result == hashes, "Verification should return current hashes"


def test_verify_integrity_mismatch(sample_files, temp_dirs):
    """Test verification when files have changed."""
    files, data_dir = sample_files
    _, state_dir = temp_dirs
    
    # Generate and save hashes
    hashes = generate_hashes(data_dir)
    save_hashes(hashes, state_dir)
    
    # Modify a file
    file_to_modify = data_dir / "test1.txt"
    file_to_modify.write_text("Modified content")
    
    # Verify should detect mismatch
    with pytest.raises(IntegrityError, match="Data integrity check failed"):
        verify_integrity(data_dir, state_dir, strict=True)
    
    # Non-strict mode should return current hashes but not raise
    result = verify_integrity(data_dir, state_dir, strict=False)
    assert "test1.txt" in result


def test_verify_integrity_missing_file(sample_files, temp_dirs):
    """Test verification when a file is missing."""
    files, data_dir = sample_files
    _, state_dir = temp_dirs
    
    # Generate and save hashes
    hashes = generate_hashes(data_dir)
    save_hashes(hashes, state_dir)
    
    # Remove a file
    file_to_remove = data_dir / "test1.txt"
    file_to_remove.unlink()
    
    # Verify should detect missing file (warning in non-strict, error in strict)
    with pytest.raises(IntegrityError):
        verify_integrity(data_dir, state_dir, strict=True)
    
    # Non-strict should succeed but log warning
    result = verify_integrity(data_dir, state_dir, strict=False)
    # The removed file should not be in the result
    assert "test1.txt" not in result


def test_update_hashes(sample_files, temp_dirs):
    """Test the update_hashes convenience function."""
    files, data_dir = sample_files
    _, state_dir = temp_dirs
    
    # Update hashes
    new_hashes = update_hashes(data_dir, state_dir)
    
    # Verify they were saved
    loaded_hashes = load_hashes(state_dir)
    assert loaded_hashes == new_hashes
