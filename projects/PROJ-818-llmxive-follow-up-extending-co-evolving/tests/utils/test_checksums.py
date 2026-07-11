"""
Unit tests for the checksum utility module.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the module functions
from src.utils.checksums import (
    compute_sha256,
    load_checksum_registry,
    register_file,
    save_checksum_registry,
    verify_file,
    update_checksums_for_files,
    PROJECT_ROOT,
    CHECKSUM_FILE_PATH,
)


@pytest.fixture
def temp_file():
    """Create a temporary file with known content for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Hello, World!")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure mimicking project data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        yield data_dir


def test_compute_sha256_known_value(temp_file):
    """Test SHA-256 computation against a known value."""
    # "Hello, World!" SHA-256 is known
    expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    computed = compute_sha256(temp_file)
    assert computed == expected_hash


def test_compute_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_sha256("/nonexistent/path/file.txt")


def test_compute_sha256_directory():
    """Test that IsADirectoryError is raised for directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(IsADirectoryError):
            compute_sha256(tmpdir)


def test_load_checksum_registry_empty():
    """Test loading registry when file does not exist."""
    # Temporarily point to a non-existent file
    original_path = CHECKSUM_FILE_PATH
    import src.utils.checksums as checksums_module
    checksums_module.CHECKSUM_FILE_PATH = Path("/nonexistent/checksums.json")

    try:
        registry = load_checksum_registry()
        assert registry == {}
    finally:
        checksums_module.CHECKSUM_FILE_PATH = original_path


def test_save_and_load_checksum_registry(temp_data_dir):
    """Test saving and loading a checksum registry."""
    test_registry = {
        "data/test.json": {
            "hash": "abc123",
            "label": "Test File",
            "source_file": "/fake/path"
        }
    }

    test_file = temp_data_dir / "test.json"
    test_file.write_text("test content")

    # Temporarily override the path
    import src.utils.checksums as checksums_module
    original_path = checksums_module.CHECKSUM_FILE_PATH
    checksums_module.CHECKSUM_FILE_PATH = temp_data_dir / "checksums.json"

    try:
        save_checksum_registry(test_registry)
        loaded = load_checksum_registry()
        assert loaded == test_registry
    finally:
        checksums_module.CHECKSUM_FILE_PATH = original_path


def test_register_file(temp_file):
    """Test registering a single file."""
    # Create a temp data directory and override path
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()

        import src.utils.checksums as checksums_module
        original_path = checksums_module.CHECKSUM_FILE_PATH
        checksums_module.CHECKSUM_FILE_PATH = data_dir / "checksums.json"

        try:
            # Copy temp file to data dir for relative path consistency
            data_file = data_dir / "test_input.txt"
            data_file.write_text("test content")

            hash_value = register_file(data_file, label="Test Input")

            # Verify hash is correct
            expected = compute_sha256(data_file)
            assert hash_value == expected

            # Verify registry was updated
            registry = load_checksum_registry()
            assert "data/test_input.txt" in registry
            assert registry["data/test_input.txt"]["hash"] == expected
            assert registry["data/test_input.txt"]["label"] == "Test Input"
        finally:
            checksums_module.CHECKSUM_FILE_PATH = original_path


def test_verify_file_success(temp_file):
    """Test successful verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()

        import src.utils.checksums as checksums_module
        original_path = checksums_module.CHECKSUM_FILE_PATH
        checksums_module.CHECKSUM_FILE_PATH = data_dir / "checksums.json"

        try:
            # Create and register file
            data_file = data_dir / "verify_test.txt"
            data_file.write_text("verify me")
            register_file(data_file)

            # Verify should return True
            assert verify_file(data_file) is True
        finally:
            checksums_module.CHECKSUM_FILE_PATH = original_path


def test_verify_file_missing_in_registry(temp_file):
    """Test verification when file is not in registry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()

        import src.utils.checksums as checksums_module
        original_path = checksums_module.CHECKSUM_FILE_PATH
        checksums_module.CHECKSUM_FILE_PATH = data_dir / "checksums.json"

        try:
            data_file = data_dir / "unregistered.txt"
            data_file.write_text("unregistered")

            # Should return False as file is not in registry
            assert verify_file(data_file) is False
        finally:
            checksums_module.CHECKSUM_FILE_PATH = original_path


def test_update_checksums_for_files():
    """Test updating checksums for multiple files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()

        import src.utils.checksums as checksums_module
        original_path = checksums_module.CHECKSUM_FILE_PATH
        checksums_module.CHECKSUM_FILE_PATH = data_dir / "checksums.json"

        try:
            # Create multiple test files
            file1 = data_dir / "multi1.txt"
            file1.write_text("content 1")
            file2 = data_dir / "multi2.txt"
            file2.write_text("content 2")

            results = update_checksums_for_files([file1, file2])

            assert len(results) == 2
            assert "data/multi1.txt" in results
            assert "data/multi2.txt" in results

            # Verify hashes are correct
            assert results["data/multi1.txt"] == compute_sha256(file1)
            assert results["data/multi2.txt"] == compute_sha256(file2)
        finally:
            checksums_module.CHECKSUM_FILE_PATH = original_path
