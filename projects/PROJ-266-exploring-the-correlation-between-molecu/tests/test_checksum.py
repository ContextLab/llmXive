"""
Unit tests for the checksum utility.
"""
import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from utils.checksum import (
    compute_file_checksum,
    load_state_file,
    save_state_file,
    register_checksum,
    scan_and_register_data_files,
    verify_checksum,
    get_logger_for_module
)
from utils.config import get_project_root


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file with known content."""
    file_path = tmp_path / "test_file.txt"
    content = b"Hello, World!"
    file_path.write_bytes(content)
    return file_path, content


@pytest.fixture
def temp_data_structure(tmp_path):
    """Create a temporary data directory structure with files."""
    data_dir = tmp_path / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)

    # Create some test files
    (raw_dir / "file1.csv").write_bytes(b"raw data 1")
    (raw_dir / "file2.csv").write_bytes(b"raw data 2")
    (processed_dir / "file3.csv").write_bytes(b"processed data")

    return tmp_path, data_dir


def test_compute_file_checksum(temp_file):
    """Test checksum computation."""
    file_path, content = temp_file
    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_file_checksum(file_path)
    assert actual_hash == expected_hash


def test_compute_file_checksum_file_not_found():
    """Test checksum computation on non-existent file."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(Path("/nonexistent/file.txt"))


def test_compute_file_checksum_unsupported_algorithm(temp_file):
    """Test checksum computation with unsupported algorithm."""
    file_path, _ = temp_file
    with pytest.raises(ValueError, match="Unsupported algorithm"):
        compute_file_checksum(file_path, algorithm="md5")


def test_load_state_file_missing():
    """Test loading state file when it doesn't exist."""
    with patch("utils.config.get_state_path") as mock_get_path:
        mock_get_path.return_value = Path("/nonexistent/state.yaml")
        state = load_state_file()
        assert "checksums" in state
        assert state["checksums"] == {}


def test_save_and_load_state_file(tmp_path):
    """Test saving and loading state file."""
    state_path = tmp_path / "state.yaml"
    state = {"checksums": {"test.txt": {"hash": "abc123", "algorithm": "sha256"}}}

    with patch("utils.config.get_state_path") as mock_get_path:
        mock_get_path.return_value = state_path
        assert save_state_file(state)
        loaded_state = load_state_file()
        assert loaded_state["checksums"]["test.txt"]["hash"] == "abc123"


def test_register_checksum(temp_file, tmp_path):
    """Test registering a checksum."""
    file_path, _ = temp_file
    state = {"checksums": {}}

    with patch("utils.config.get_project_root") as mock_get_root:
        mock_get_root.return_value = tmp_path
        register_checksum(file_path, state)

    assert len(state["checksums"]) == 1
    assert "test_file.txt" in state["checksums"]
    assert "hash" in state["checksums"]["test_file.txt"]


def test_scan_and_register_data_files(temp_data_structure):
    """Test scanning and registering data files."""
    tmp_path, data_dir = temp_data_structure

    with patch("utils.config.get_project_root") as mock_get_root:
        mock_get_root.return_value = tmp_path
        with patch("utils.config.get_state_path") as mock_get_state:
            state_file = tmp_path / "state.yaml"
            mock_get_state.return_value = state_file
            registered = scan_and_register_data_files()

    assert len(registered) == 3
    assert "data/raw/file1.csv" in registered
    assert "data/raw/file2.csv" in registered
    assert "data/processed/file3.csv" in registered


def test_verify_checksum_success(temp_file, tmp_path):
    """Test successful checksum verification."""
    file_path, content = temp_file
    expected_hash = hashlib.sha256(content).hexdigest()

    with patch("utils.config.get_project_root") as mock_get_root:
        mock_get_root.return_value = tmp_path
        with patch("utils.config.get_state_path") as mock_get_state:
            state_file = tmp_path / "state.yaml"
            mock_get_state.return_value = state_file
            # First register the checksum
            state = {"checksums": {}}
            from utils.checksum import register_checksum
            register_checksum(file_path, state)
            save_state_file(state)

    # Now verify
    assert verify_checksum(file_path)


def test_verify_checksum_mismatch(temp_file, tmp_path):
    """Test checksum verification with mismatch."""
    file_path, content = temp_file
    # Register a wrong hash
    state = {"checksums": {"test_file.txt": {"hash": "wrong_hash", "algorithm": "sha256"}}}

    with patch("utils.config.get_project_root") as mock_get_root:
        mock_get_root.return_value = tmp_path
        with patch("utils.config.get_state_path") as mock_get_state:
            state_file = tmp_path / "state.yaml"
            mock_get_state.return_value = state_file
            save_state_file(state)

    # Verify should return False
    assert not verify_checksum(file_path)


def test_verify_checksum_file_not_found():
    """Test verification on non-existent file."""
    with pytest.raises(FileNotFoundError):
        verify_checksum(Path("/nonexistent/file.txt"))


def test_get_logger_for_module():
    """Test getting logger for the module."""
    logger = get_logger_for_module()
    assert logger is not None
    assert logger.name == "utils.checksum"