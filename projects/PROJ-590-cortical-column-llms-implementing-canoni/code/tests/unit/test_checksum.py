import os
import json
import tempfile
import pytest
from pathlib import Path
import hashlib

# Import the module under test
from src.utils.checksum import calculate_sha256, find_files, generate_checksums, verify_checksums

def test_calculate_sha256():
    """Test SHA256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test data")
        temp_path = f.name

    try:
        expected_hash = hashlib.sha256(b"test data").hexdigest()
        actual_hash = calculate_sha256(Path(temp_path))
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)

def test_find_files():
    """Test file discovery."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        # Create structure
        (tmppath / "subdir").mkdir()
        (tmppath / "file1.txt").touch()
        (tmppath / "file2.log").touch()
        (tmppath / "subdir" / "file3.txt").touch()

        # Test all files
        files = find_files(tmppath)
        assert len(files) == 3

        # Test extension filter
        txt_files = find_files(tmppath, extensions=[".txt"])
        assert len(txt_files) == 2
        assert all(f.suffix == ".txt" for f in txt_files)

def test_generate_and_verify_checksums():
    """Test the full cycle of generating and verifying checksums."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        # Create test files
        (tmppath / "data").mkdir()
        (tmppath / "data" / "config.json").write_text('{"key": "value"}')
        (tmppath / "state").mkdir()
        (tmppath / "state" / "state.yaml").write_text('status: running')

        output_file = tmppath / "checksums.json"
        target_dirs = [tmppath / "data", tmppath / "state"]

        # Generate
        checksums = generate_checksums(target_dirs, output_file)
        assert output_file.exists()
        assert len(checksums) == 2

        # Verify (should pass)
        assert verify_checksums(output_file, target_dirs) is True

        # Modify a file
        (tmppath / "data" / "config.json").write_text('{"key": "changed"}')

        # Verify (should fail)
        assert verify_checksums(output_file, target_dirs) is False

def test_nonexistent_directory():
    """Test handling of non-existent directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        output_file = tmppath / "checksums.json"
        # Pass a directory that doesn't exist
        target_dirs = [tmppath / "nonexistent"]
        
        # Should not crash, just return empty or log warning
        checksums = generate_checksums(target_dirs, output_file)
        assert checksums == {}