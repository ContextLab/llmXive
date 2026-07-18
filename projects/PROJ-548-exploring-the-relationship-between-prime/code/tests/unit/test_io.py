import pytest
import os
import sys
import tempfile
import time
from pathlib import Path
import yaml
import hashlib

# Adjust import to match project structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.io import (
    compute_file_checksum,
    compute_directory_checksum,
    load_state,
    save_state,
    update_state_checksums,
    verify_data_integrity,
    get_data_change_summary,
    commit_state,
    _get_state_path
)
from src.utils.config import get_project_paths

@pytest.fixture
def temp_state_dir(tmp_path):
    """Creates a temporary directory structure mimicking the project state."""
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    return state_dir

@pytest.fixture
def sample_file(tmp_path):
    """Creates a sample file for checksum testing."""
    file_path = tmp_path / "test.txt"
    content = "Hello, World! This is a test file for checksumming."
    file_path.write_text(content)
    return file_path

class TestComputeFileChecksum:
    def test_sha256_correctness(self, sample_file):
        """Verify that the computed hash matches the expected SHA-256."""
        content = sample_file.read_text()
        expected_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        actual_hash = compute_file_checksum(sample_file)
        assert actual_hash == expected_hash

    def test_file_not_found(self, tmp_path):
        """Verify that FileNotFoundError is raised for missing files."""
        missing_path = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(missing_path)

    def test_large_file_handling(self, tmp_path):
        """Verify that large files are handled correctly (chunked reading)."""
        large_file = tmp_path / "large.bin"
        # Create a 2MB file
        content = b"x" * (2 * 1024 * 1024)
        large_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_file_checksum(large_file)
        assert actual_hash == expected_hash

class TestComputeDirectoryChecksum:
    def test_empty_directory(self, tmp_path):
        """Directory with no files should produce a deterministic hash."""
        hash1 = compute_directory_checksum(tmp_path)
        hash2 = compute_directory_checksum(tmp_path)
        assert hash1 == hash2
        assert len(hash1) == 64 # SHA-256 hex length

    def test_directory_with_files(self, tmp_path):
        """Directory checksum should change if files change."""
        file1 = tmp_path / "a.txt"
        file1.write_text("content A")
        
        hash_with_a = compute_directory_checksum(tmp_path)
        
        file2 = tmp_path / "b.txt"
        file2.write_text("content B")
        
        hash_with_b = compute_directory_checksum(tmp_path)
        
        assert hash_with_a != hash_with_b

    def test_file_content_change(self, tmp_path):
        """Directory checksum should change if file content changes."""
        file1 = tmp_path / "test.txt"
        file1.write_text("original")
        hash1 = compute_directory_checksum(tmp_path)
        
        file1.write_text("modified")
        hash2 = compute_directory_checksum(tmp_path)
        
        assert hash1 != hash2

class TestStateManagement:
    def test_load_nonexistent_state(self, tmp_path, monkeypatch):
        """Loading a non-existent state should return empty dict."""
        # Mock _get_state_path to return a path that doesn't exist
        def mock_get_path():
            return tmp_path / "nonexistent.yaml"
        monkeypatch.setattr("src.utils.io._get_state_path", mock_get_path)
        
        state = load_state()
        assert state == {}

    def test_save_and_load_state(self, tmp_path, monkeypatch):
        """Verify save_state and load_state roundtrip."""
        test_data = {"key": "value", "nested": {"a": 1}}
        
        def mock_get_path():
            return tmp_path / "test_state.yaml"
        monkeypatch.setattr("src.utils.io._get_state_path", mock_get_path)
        
        save_state(test_data)
        loaded_data = load_state()
        
        assert loaded_data == test_data

    def test_save_creates_directories(self, tmp_path, monkeypatch):
        """Save state should create parent directories if missing."""
        deep_path = tmp_path / "deep" / "nested" / "state.yaml"
        
        def mock_get_path():
            return deep_path
        monkeypatch.setattr("src.utils.io._get_state_path", mock_get_path)
        
        save_state({"data": 1})
        assert deep_path.exists()

class TestChecksumUpdates:
    def test_update_checksums_adds_metadata(self, tmp_path, monkeypatch):
        """update_state_checksums should add metadata if missing."""
        def mock_get_path():
            return tmp_path / "state.yaml"
        monkeypatch.setattr("src.utils.io._get_state_path", mock_get_path)
        
        initial_state = {}
        updated = update_state_checksums(initial_state)
        
        assert "metadata" in updated
        assert "last_checksum_update" in updated["metadata"]

    def test_update_checksums_removes_missing_files(self, tmp_path, monkeypatch):
        """If a file in checksums is missing, it should be removed from state."""
        # Create a fake state with a checksum for a file that doesn't exist
        fake_state = {
            "checksums": {
                "fake_file": {
                    "path": "data/processed/nonexistent.csv",
                    "sha256": "abc123"
                }
            }
        }
        
        def mock_get_path():
            return tmp_path / "state.yaml"
        monkeypatch.setattr("src.utils.io._get_state_path", mock_get_path)
        
        updated = update_state_checksums(fake_state)
        
        # The missing file should be removed from the checksums dict
        assert "fake_file" not in updated.get("checksums", {})

class TestChangeSummary:
    def test_summary_generation(self, tmp_path, monkeypatch):
        """Verify that get_data_change_summary returns a formatted string."""
        def mock_get_path():
            return tmp_path / "state.yaml"
        monkeypatch.setattr("src.utils.io._get_state_path", mock_get_path)
        
        # Create a valid state
        save_state({"checksums": {}})
        
        summary = get_data_change_summary()
        assert "Data Integrity Report" in summary
        assert "Overall Status" in summary

class TestVerifyDataIntegrity:
    def test_verify_valid_file(self, tmp_path, monkeypatch):
        """Verify integrity returns True for a valid file."""
        # Create a real file
        data_file = tmp_path / "data" / "processed"
        data_file.mkdir(parents=True)
        target_file = data_file / "test.csv"
        target_file.write_text("col1,col2\n1,2")
        
        # Compute real hash
        real_hash = compute_file_checksum(target_file)
        
        state = {
            "checksums": {
                "test_file": {
                    "path": "data/processed/test.csv",
                    "sha256": real_hash
                }
            }
        }
        
        def mock_get_path():
            return tmp_path / "state.yaml"
        monkeypatch.setattr("src.utils.io._get_state_path", mock_get_path)
        
        # Mock get_project_paths to return tmp_path as base
        def mock_paths():
            return tmp_path, None
        monkeypatch.setattr("src.utils.io.get_project_paths", mock_paths)
        
        is_valid, details = verify_data_integrity(state)
        
        assert is_valid is True
        assert details["test_file"] == "Valid"

    def test_verify_corrupted_file(self, tmp_path, monkeypatch):
        """Verify integrity returns False if file content changed."""
        data_file = tmp_path / "data" / "processed"
        data_file.mkdir(parents=True)
        target_file = data_file / "test.csv"
        target_file.write_text("original content")
        
        original_hash = compute_file_checksum(target_file)
        
        # Corrupt the file
        target_file.write_text("corrupted content")
        
        state = {
            "checksums": {
                "test_file": {
                    "path": "data/processed/test.csv",
                    "sha256": original_hash
                }
            }
        }
        
        def mock_get_path():
            return tmp_path / "state.yaml"
        monkeypatch.setattr("src.utils.io._get_state_path", mock_get_path)
        
        def mock_paths():
            return tmp_path, None
        monkeypatch.setattr("src.utils.io.get_project_paths", mock_paths)
        
        is_valid, details = verify_data_integrity(state)
        
        assert is_valid is False
        assert "Corrupted" in details["test_file"]

    def test_verify_missing_file(self, tmp_path, monkeypatch):
        """Verify integrity returns False if file is missing."""
        state = {
            "checksums": {
                "missing_file": {
                    "path": "data/processed/never_existed.csv",
                    "sha256": "abc123"
                }
            }
        }
        
        def mock_get_path():
            return tmp_path / "state.yaml"
        monkeypatch.setattr("src.utils.io._get_state_path", mock_get_path)
        
        def mock_paths():
            return tmp_path, None
        monkeypatch.setattr("src.utils.io.get_project_paths", mock_paths)
        
        is_valid, details = verify_data_integrity(state)
        
        assert is_valid is False
        assert details["missing_file"] == "File missing"
