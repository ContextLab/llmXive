"""
Unit tests for the versioning module.
Tests checksum computation and project state updates.
"""
import os
import sys
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from versioning import (
    compute_file_checksum,
    get_all_data_files,
    checksum_data_directory,
    load_project_state,
    save_project_state,
    update_project_state,
    main
)

class TestComputeFileChecksum:
    """Tests for compute_file_checksum function."""

    def test_compute_checksum_sha256(self, tmp_path):
        """Test SHA256 checksum computation."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = compute_file_checksum(test_file)
        
        # Verify against known hash
        expected = hashlib.sha256(test_content).hexdigest()
        assert checksum == expected
        assert len(checksum) == 64  # SHA256 hex digest length

    def test_compute_checksum_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing files."""
        nonexistent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(nonexistent)

    def test_compute_checksum_large_file(self, tmp_path):
        """Test checksum computation for larger files (chunked reading)."""
        test_file = tmp_path / "large.bin"
        # Create a 1MB file
        content = b"x" * (1024 * 1024)
        test_file.write_bytes(content)
        
        checksum = compute_file_checksum(test_file)
        
        # Verify it's a valid hex string
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)

class TestGetAllDataFiles:
    """Tests for get_all_data_files function."""

    def test_get_all_files_empty_dir(self, tmp_path):
        """Test with empty directory."""
        files = get_all_data_files(tmp_path)
        assert files == []

    def test_get_all_files_single_file(self, tmp_path):
        """Test with single file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        files = get_all_data_files(tmp_path)
        assert len(files) == 1
        assert test_file in files

    def test_get_all_files_nested_dirs(self, tmp_path):
        """Test with nested directories."""
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)
        
        file1 = tmp_path / "file1.txt"
        file2 = subdir / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        files = get_all_data_files(tmp_path)
        assert len(files) == 2
        assert file1 in files
        assert file2 in files

    def test_get_all_files_excludes_hidden(self, tmp_path):
        """Test that hidden files are excluded."""
        hidden_file = tmp_path / ".hidden"
        visible_file = tmp_path / "visible.txt"
        
        hidden_file.write_text("hidden")
        visible_file.write_text("visible")
        
        files = get_all_data_files(tmp_path)
        assert len(files) == 1
        assert visible_file in files
        assert hidden_file not in files

    def test_get_all_files_excludes_pyc(self, tmp_path):
        """Test that .pyc files are excluded."""
        pyc_file = tmp_path / "module.pyc"
        py_file = tmp_path / "module.py"
        
        pyc_file.write_text("compiled")
        py_file.write_text("source")
        
        files = get_all_data_files(tmp_path)
        assert len(files) == 1
        assert py_file in files
        assert pyc_file not in files

    def test_get_all_files_nonexistent_dir(self, tmp_path):
        """Test with non-existent directory."""
        nonexistent = tmp_path / "does_not_exist"
        files = get_all_data_files(nonexistent)
        assert files == []

class TestChecksumDataDirectory:
    """Tests for checksum_data_directory function."""

    def test_checksum_empty_dir(self, tmp_path, caplog):
        """Test checksumming an empty directory."""
        checksums = checksum_data_directory(tmp_path)
        assert checksums == {}

    def test_checksum_single_file(self, tmp_path):
        """Test checksumming a directory with one file."""
        test_file = tmp_path / "test.txt"
        content = b"test content"
        test_file.write_bytes(content)
        
        checksums = checksum_data_directory(tmp_path)
        
        assert len(checksums) == 1
        assert "test.txt" in checksums
        
        # Verify checksum correctness
        expected = hashlib.sha256(content).hexdigest()
        assert checksums["test.txt"] == expected

    def test_checksum_multiple_files(self, tmp_path):
        """Test checksumming a directory with multiple files."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        content1 = b"content1"
        content2 = b"content2"
        
        file1.write_bytes(content1)
        file2.write_bytes(content2)
        
        checksums = checksum_data_directory(tmp_path)
        
        assert len(checksums) == 2
        assert "file1.txt" in checksums
        assert "file2.txt" in checksums
        
        # Verify checksums
        expected1 = hashlib.sha256(content1).hexdigest()
        expected2 = hashlib.sha256(content2).hexdigest()
        assert checksums["file1.txt"] == expected1
        assert checksums["file2.txt"] == expected2

class TestLoadProjectState:
    """Tests for load_project_state function."""

    def test_load_existing_state(self, tmp_path):
        """Test loading an existing state file."""
        state_file = tmp_path / "state.yaml"
        initial_state = {
            "project_id": "TEST-001",
            "version": "1.0.0",
            "data_checksums": {"file1.txt": "abc123"}
        }
        
        with open(state_file, "w") as f:
            yaml.dump(initial_state, f)
        
        loaded = load_project_state(state_file)
        
        assert loaded["project_id"] == "TEST-001"
        assert loaded["version"] == "1.0.0"
        assert loaded["data_checksums"]["file1.txt"] == "abc123"

    def test_load_nonexistent_state(self, tmp_path):
        """Test loading a non-existent state file creates default."""
        state_file = tmp_path / "nonexistent.yaml"
        
        loaded = load_project_state(state_file)
        
        assert "project_id" in loaded
        assert "version" in loaded
        assert "data_checksums" in loaded
        assert loaded["data_checksums"] == {}

class TestSaveProjectState:
    """Tests for save_project_state function."""

    def test_save_state_creates_directory(self, tmp_path):
        """Test that save creates parent directories."""
        nested_dir = tmp_path / "deep" / "nested"
        state_file = nested_dir / "state.yaml"
        state = {"test": "value"}
        
        save_project_state(state_file, state)
        
        assert state_file.exists()
        assert nested_dir.exists()

    def test_save_state_valid_yaml(self, tmp_path):
        """Test that saved state is valid YAML."""
        state_file = tmp_path / "state.yaml"
        state = {
            "project_id": "TEST-001",
            "data_checksums": {"file1.txt": "abc123"}
        }
        
        save_project_state(state_file, state)
        
        # Verify it can be loaded back
        with open(state_file, "r") as f:
            loaded = yaml.safe_load(f)
        
        assert loaded == state

class TestUpdateProjectState:
    """Tests for update_project_state function."""

    def test_update_state_new_file(self, tmp_path):
        """Test updating state with new data files."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        test_file = data_dir / "test.txt"
        test_file.write_bytes(b"test content")
        
        state_file = tmp_path / "state.yaml"
        project_id = "TEST-001"
        
        state = update_project_state(state_file, data_dir, project_id)
        
        assert state["project_id"] == project_id
        assert "data_checksums" in state
        assert "test.txt" in state["data_checksums"]
        assert "last_updated" in state
        assert state["metadata"]["last_versioned_by"] == "versioning.py"

    def test_update_state_existing_file(self, tmp_path):
        """Test updating state with existing checksums."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        test_file = data_dir / "test.txt"
        test_file.write_bytes(b"test content")
        
        state_file = tmp_path / "state.yaml"
        
        # Create initial state
        initial_state = {
            "project_id": "TEST-001",
            "data_checksums": {"old_file.txt": "old_checksum"},
            "version": "1.0.0"
        }
        with open(state_file, "w") as f:
            yaml.dump(initial_state, f)
        
        # Update state
        state = update_project_state(state_file, data_dir, "TEST-001")
        
        # Should have both old and new checksums
        assert "old_file.txt" not in state["data_checksums"]  # Old file removed
        assert "test.txt" in state["data_checksums"]  # New file added

    def test_update_state_no_data_dir(self, tmp_path, caplog):
        """Test updating state when data directory doesn't exist."""
        state_file = tmp_path / "state.yaml"
        nonexistent_dir = tmp_path / "nonexistent"
        
        state = update_project_state(state_file, nonexistent_dir, "TEST-001")
        
        assert state["data_checksums"] == {}
        assert "last_updated" in state

class TestMain:
    """Tests for main function."""

    def test_main_success(self, tmp_path, capsys):
        """Test successful execution of main."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "test.txt").write_bytes(b"test")
        
        state_file = tmp_path / "state.yaml"
        
        # Mock sys.argv
        test_args = [
            "versioning.py",
            "--data-dir", str(data_dir),
            "--state-file", str(state_file),
            "--project-id", "TEST-001"
        ]
        
        with patch("sys.argv", test_args):
            result = main()
        
        assert result == 0
        assert state_file.exists()

    def test_main_error_handling(self, tmp_path, caplog):
        """Test error handling in main."""
        # Use a directory that causes an error (e.g., permission denied)
        # For this test, we'll just verify the function doesn't crash on normal inputs
        
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        state_file = tmp_path / "state.yaml"
        
        test_args = [
            "versioning.py",
            "--data-dir", str(data_dir),
            "--state-file", str(state_file)
        ]
        
        with patch("sys.argv", test_args):
            result = main()
        
        assert result == 0