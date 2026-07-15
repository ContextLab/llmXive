"""
tests/unit/test_download.py
Unit tests for code/download.py functionality.
"""
import hashlib
import json
import tempfile
import os
from pathlib import Path
import pytest

# Import the module under test
# Note: In a real test runner, we might need to adjust sys.path
from download import calculate_sha256, save_checksums, load_saved_checksums, verify_checksums

def test_calculate_sha256():
    """Test SHA-256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)

    try:
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        actual_hash = calculate_sha256(temp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)

def test_save_and_load_checksums():
    """Test saving and loading checksums."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        checksums_file = Path(tmpdir) / "checksums.json"

        # Create a dummy file
        test_file = data_dir / "test.txt"
        test_file.write_text("Test content")

        # Save checksums
        save_checksums(data_dir, checksums_file)

        # Load checksums
        loaded_checksums = load_saved_checksums(checksums_file)

        # Verify
        assert "test.txt" in loaded_checksums
        expected_hash = hashlib.sha256(b"Test content").hexdigest()
        assert loaded_checksums["test.txt"] == expected_hash

def test_verify_checksums_success():
    """Test verification when checksums match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        checksums_file = Path(tmpdir) / "checksums.json"

        test_file = data_dir / "test.txt"
        test_file.write_text("Valid content")

        # Save valid checksums
        save_checksums(data_dir, checksums_file)

        # Verify
        assert verify_checksums(data_dir, checksums_file) is True

def test_verify_checksums_failure():
    """Test verification when checksums do not match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        checksums_file = Path(tmpdir) / "checksums.json"

        test_file = data_dir / "test.txt"
        test_file.write_text("Original content")

        # Save checksums
        save_checksums(data_dir, checksums_file)

        # Modify file
        test_file.write_text("Modified content")

        # Verify should fail
        assert verify_checksums(data_dir, checksums_file) is False

def test_verify_checksums_missing_file():
    """Test verification when a file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        checksums_file = Path(tmpdir) / "checksums.json"

        test_file = data_dir / "test.txt"
        test_file.write_text("Content")

        # Save checksums
        save_checksums(data_dir, checksums_file)

        # Delete file
        test_file.unlink()

        # Verify should fail
        assert verify_checksums(data_dir, checksums_file) is False
