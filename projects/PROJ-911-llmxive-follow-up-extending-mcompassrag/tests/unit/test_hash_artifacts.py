"""
Unit tests for code/utils/hash_artifacts.py
"""
import os
import tempfile
import json
import yaml
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from code.utils.hash_artifacts import calculate_sha256, hash_directory, update_state_file
from code.config import DATA_DIR, PROJECT_ROOT

class TestCalculateSha256:
    """Tests for the calculate_sha256 function."""

    def test_calculate_sha256_known_file(self):
        """Test hashing a file with known content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_path = Path(f.name)

        try:
            # Known SHA-256 for "Hello, World!"
            expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            result = calculate_sha256(temp_path)
            assert result == expected_hash
        finally:
            temp_path.unlink()

    def test_calculate_sha256_empty_file(self):
        """Test hashing an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = Path(f.name)

        try:
            # Known SHA-256 for empty file
            expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            result = calculate_sha256(temp_path)
            assert result == expected_hash
        finally:
            temp_path.unlink()

    def test_calculate_sha256_binary_file(self):
        """Test hashing a binary file."""
        binary_content = b'\x00\x01\x02\x03\x04\x05'
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
            f.write(binary_content)
            temp_path = Path(f.name)

        try:
            result = calculate_sha256(temp_path)
            assert len(result) == 64  # SHA-256 hex string length
            assert all(c in '0123456789abcdef' for c in result)
        finally:
            temp_path.unlink()

class TestHashDirectory:
    """Tests for the hash_directory function."""

    def test_hash_directory_empty(self):
        """Test hashing an empty directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            result = hash_directory(dir_path)
            assert result == {}

    def test_hash_directory_single_file(self):
        """Test hashing a directory with a single file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            file_path = dir_path / "test.txt"
            file_path.write_text("test content")

            result = hash_directory(dir_path)
            assert "test.txt" in result
            assert len(result["test.txt"]) == 64

    def test_hash_directory_nested(self):
        """Test hashing a directory with nested files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            subdir = dir_path / "subdir"
            subdir.mkdir()

            file1 = dir_path / "file1.txt"
            file1.write_text("content1")

            file2 = subdir / "file2.txt"
            file2.write_text("content2")

            result = hash_directory(dir_path)
            assert "file1.txt" in result
            assert "subdir/file2.txt" in result
            assert len(result) == 2

    def test_hash_directory_nonexistent(self):
        """Test hashing a non-existent directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir) / "nonexistent"
            result = hash_directory(dir_path)
            assert result == {}

class TestUpdateStateFile:
    """Tests for the update_state_file function."""

    @patch('code.utils.hash_artifacts.hash_directory')
    @patch('code.utils.hash_artifacts.yaml.dump')
    @patch('builtins.open', new_callable=MagicMock)
    def test_update_state_file_creates_structure(self, mock_open, mock_yaml_dump, mock_hash_dir):
        """Test that update_state_file creates the state directory and writes the file."""
        # Mock hash_directory to return empty dict
        mock_hash_dir.return_value = {}

        # Mock the file open context manager
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Create a temporary directory to act as PROJECT_ROOT and DATA_DIR
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Patch PROJECT_ROOT and DATA_DIR
            with patch('code.utils.hash_artifacts.PROJECT_ROOT', tmp_path), \
                 patch('code.utils.hash_artifacts.DATA_DIR', tmp_path / "data"):

                # Ensure data directories exist
                (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
                (tmp_path / "data" / "results").mkdir(parents=True, exist_ok=True)
                (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)

                update_state_file()

                # Verify state directory was created
                state_dir = tmp_path / "state" / "projects"
                assert state_dir.exists()

                # Verify update_state_file was called (which triggers file write)
                mock_open.assert_called()
                mock_yaml_dump.assert_called()

    @patch('code.utils.hash_artifacts.hash_directory')
    @patch('code.utils.hash_artifacts.yaml.dump')
    @patch('builtins.open', new_callable=MagicMock)
    def test_update_state_file_includes_hashes(self, mock_open, mock_yaml_dump, mock_hash_dir):
        """Test that update_state_file includes hashes from data directories."""
        # Mock hash_directory to return sample hashes
        mock_hash_dir.return_value = {"file1.txt": "abc123..."}

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            with patch('code.utils.hash_artifacts.PROJECT_ROOT', tmp_path), \
                 patch('code.utils.hash_artifacts.DATA_DIR', tmp_path / "data"):

                (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)

                update_state_file()

                # Verify yaml.dump was called with a dict containing artifacts
                call_args = mock_yaml_dump.call_args
                assert call_args is not None
                state_data = call_args[0][0]
                assert "artifacts" in state_data
                assert "processed" in state_data["artifacts"]

    @patch('code.utils.hash_artifacts.hash_directory')
    @patch('code.utils.hash_artifacts.yaml.dump')
    @patch('builtins.open', new_callable=MagicMock)
    def test_update_state_file_skips_missing_dirs(self, mock_open, mock_yaml_dump, mock_hash_dir):
        """Test that update_state_file handles missing data directories gracefully."""
        # Mock hash_directory to return empty dict (simulating missing dir)
        mock_hash_dir.return_value = {}

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            with patch('code.utils.hash_artifacts.PROJECT_ROOT', tmp_path), \
                 patch('code.utils.hash_artifacts.DATA_DIR', tmp_path / "data"):

                # Don't create data directories - they should be skipped

                update_state_file()

                # Verify the function completed without error
                assert mock_open.called