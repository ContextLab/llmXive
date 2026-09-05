import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from checksum_manager import (
    calculate_sha256,
    generate_dataset_checksums,
    update_state_with_checksums,
    validate_existing_checksums,
)
from state_manager import load_state, save_state


class TestCalculateSha256:
    def test_calculate_sha256_simple_file(self, tmp_path):
        """Test SHA-256 calculation on a simple file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        expected_hash = hashlib.sha256(test_content).hexdigest()
        actual_hash = calculate_sha256(test_file)

        assert actual_hash == expected_hash

    def test_calculate_sha256_large_file(self, tmp_path):
        """Test SHA-256 calculation on a larger file to ensure chunking works."""
        test_file = tmp_path / "large.bin"
        # Create a file larger than the chunk size (4096 bytes)
        content = b"X" * (4096 * 3)  # 12KB file
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_sha256(test_file)

        assert actual_hash == expected_hash

    def test_calculate_sha256_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        with pytest.raises(FileNotFoundError):
            calculate_sha256(Path("non_existent_file.txt"))


class TestGenerateDatasetChecksums:
    def test_generate_checksums_single_file(self, tmp_path):
        """Test checksum generation for a single file."""
        test_file = tmp_path / "file1.txt"
        test_file.write_bytes(b"test content")

        checksums = generate_dataset_checksums(tmp_path)

        assert len(checksums) == 1
        assert "file1.txt" in checksums
        assert isinstance(checksums["file1.txt"], str)
        assert len(checksums["file1.txt"]) == 64  # SHA-256 hex length

    def test_generate_checksums_nested_directories(self, tmp_path):
        """Test checksum generation for files in nested directories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        file1 = tmp_path / "file1.txt"
        file2 = subdir / "file2.txt"
        
        file1.write_bytes(b"content1")
        file2.write_bytes(b"content2")

        checksums = generate_dataset_checksums(tmp_path)

        assert len(checksums) == 2
        assert "file1.txt" in checksums
        assert "subdir/file2.txt" in checksums or "subdir\\file2.txt" in checksums

    def test_generate_checksums_empty_directory(self, tmp_path):
        """Test checksum generation for an empty directory."""
        checksums = generate_dataset_checksums(tmp_path)
        assert checksums == {}

    def test_generate_checksums_nonexistent_directory(self):
        """Test that FileNotFoundError is raised for non-existent directory."""
        with pytest.raises(FileNotFoundError):
            generate_dataset_checksums(Path("non_existent_dir"))


class TestUpdateStateWithChecksums:
    def test_update_state_creates_artifact_hashes(self, tmp_path, monkeypatch):
        """Test that update_state creates artifact_hashes if it doesn't exist."""
        # Mock state to start empty
        mock_state = {}
        
        with patch('checksum_manager.load_state', return_value=mock_state), \
             patch('checksum_manager.save_state') as mock_save:
            
            test_checksums = {"file.txt": "abc123"}
            result = update_state_with_checksums(test_checksums)
            
            assert result is True
            mock_save.assert_called_once()
            
            # Verify the state was updated correctly
            saved_state = mock_save.call_args[0][0]
            assert "artifact_hashes" in saved_state
            assert "dataset_files" in saved_state["artifact_hashes"]
            assert saved_state["artifact_hashes"]["dataset_files"] == test_checksums
            assert "last_updated" in saved_state["artifact_hashes"]

    def test_update_state_updates_existing_artifact_hashes(self, tmp_path, monkeypatch):
        """Test that update_state updates existing artifact_hashes."""
        mock_state = {
            "artifact_hashes": {
                "dataset_files": {"old.txt": "old_hash"}
            }
        }
        
        with patch('checksum_manager.load_state', return_value=mock_state), \
             patch('checksum_manager.save_state') as mock_save:
            
            test_checksums = {"new.txt": "new_hash"}
            update_state_with_checksums(test_checksums)
            
            saved_state = mock_save.call_args[0][0]
            assert saved_state["artifact_hashes"]["dataset_files"] == test_checksums


class TestValidateExistingChecksums:
    def test_validate_existing_checksums(self, tmp_path, monkeypatch):
        """Test validation of existing checksums."""
        # Create a temporary file
        test_file = tmp_path / "test.txt"
        test_content = b"test content"
        test_file.write_bytes(test_content)
        
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        mock_state = {
            "artifact_hashes": {
                "dataset_files": {
                    "test.txt": expected_hash
                }
            }
        }
        
        # Mock the data directory path
        with patch('checksum_manager.load_state', return_value=mock_state), \
             patch('checksum_manager.Path', return_value=tmp_path):
            
            results = validate_existing_checksums()
            
            assert "test.txt" in results
            assert results["test.txt"] is True

    def test_validate_existing_checksums_mismatch(self, tmp_path, monkeypatch):
        """Test validation when checksums don't match."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")
        
        mock_state = {
            "artifact_hashes": {
                "dataset_files": {
                    "test.txt": "wrong_hash"
                }
            }
        }
        
        with patch('checksum_manager.load_state', return_value=mock_state), \
             patch('checksum_manager.Path', return_value=tmp_path):
            
            results = validate_existing_checksums()
            
            assert "test.txt" in results
            assert results["test.txt"] is False

    def test_validate_existing_checksums_missing_file(self, tmp_path, monkeypatch):
        """Test validation when file is missing."""
        mock_state = {
            "artifact_hashes": {
                "dataset_files": {
                    "missing.txt": "some_hash"
                }
            }
        }
        
        with patch('checksum_manager.load_state', return_value=mock_state), \
             patch('checksum_manager.Path', return_value=tmp_path):
            
            results = validate_existing_checksums()
            
            assert "missing.txt" in results
            assert results["missing.txt"] is False

    def test_validate_existing_checksums_no_artifact_hashes(self, tmp_path, monkeypatch):
        """Test validation when state has no artifact_hashes."""
        mock_state = {}
        
        with patch('checksum_manager.load_state', return_value=mock_state):
            results = validate_existing_checksums()
            assert results == {}