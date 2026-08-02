"""
Unit tests for the checksum_manager module.
"""
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
from checksum_manager import (
    calculate_sha256,
    generate_dataset_checksums,
    update_state_with_checksums,
    validate_existing_checksums
)


class TestCalculateSha256:
    """Tests for the calculate_sha256 function."""

    def test_calculate_sha256_simple_file(self, tmp_path):
        """Test SHA-256 calculation for a simple file."""
        # Create a test file with known content
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        # Calculate expected hash manually
        expected_hash = hashlib.sha256(content).hexdigest()

        # Calculate using our function
        actual_hash = calculate_sha256(test_file)

        assert actual_hash == expected_hash

    def test_calculate_sha256_large_file(self, tmp_path):
        """Test SHA-256 calculation for a larger file (tests chunking)."""
        # Create a larger test file (1MB)
        test_file = tmp_path / "large.bin"
        content = b"X" * (1024 * 1024)  # 1MB
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_sha256(test_file)

        assert actual_hash == expected_hash

    def test_calculate_sha256_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing files."""
        missing_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            calculate_sha256(missing_file)


class TestGenerateDatasetChecksums:
    """Tests for the generate_dataset_checksums function."""

    def test_generate_checksums_single_file(self, tmp_path):
        """Test checksum generation for a single file."""
        # Create a mock raw data directory structure
        raw_data_dir = tmp_path / "data" / "raw"
        raw_data_dir.mkdir(parents=True)
        
        test_file = raw_data_dir / "test.dat"
        content = b"test content"
        test_file.write_bytes(content)

        # Generate checksums
        checksums = generate_dataset_checksums(raw_data_dir)

        # Verify results
        assert len(checksums) == 1
        expected_key = "data/raw/test.dat"
        assert expected_key in checksums
        
        # Verify hash correctness
        expected_hash = hashlib.sha256(content).hexdigest()
        assert checksums[expected_key] == expected_hash

    def test_generate_checksums_nested_directories(self, tmp_path):
        """Test checksum generation for files in nested directories."""
        # Create nested directory structure
        raw_data_dir = tmp_path / "data" / "raw"
        (raw_data_dir / "subdir1" / "subdir2").mkdir(parents=True)
        
        # Create files at different levels
        file1 = raw_data_dir / "file1.dat"
        file1.write_bytes(b"content1")
        
        file2 = raw_data_dir / "subdir1" / "file2.dat"
        file2.write_bytes(b"content2")
        
        file3 = raw_data_dir / "subdir1" / "subdir2" / "file3.dat"
        file3.write_bytes(b"content3")

        # Generate checksums
        checksums = generate_dataset_checksums(raw_data_dir)

        # Verify all files are included
        assert len(checksums) == 3
        assert "data/raw/file1.dat" in checksums
        assert "data/raw/subdir1/file2.dat" in checksums
        assert "data/raw/subdir1/subdir2/file3.dat" in checksums

    def test_generate_checksums_empty_directory(self, tmp_path):
        """Test checksum generation for an empty directory."""
        raw_data_dir = tmp_path / "data" / "raw"
        raw_data_dir.mkdir(parents=True)

        checksums = generate_dataset_checksums(raw_data_dir)

        assert checksums == {}

    def test_generate_checksums_directory_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing directory."""
        missing_dir = tmp_path / "nonexistent" / "raw"
        
        with pytest.raises(FileNotFoundError):
            generate_dataset_checksums(missing_dir)


class TestUpdateStateWithChecksums:
    """Tests for the update_state_with_checksums function."""

    @patch('checksum_manager.load_state')
    @patch('checksum_manager.save_state')
    def test_update_state_adds_checksums(self, mock_save, mock_load, tmp_path):
        """Test that checksums are added to state file."""
        # Setup mock state
        initial_state = {
            'project': 'test-project',
            'last_updated': '2024-01-01'
        }
        mock_load.return_value = initial_state.copy()
        
        state_file = tmp_path / "state.yaml"
        checksums = {
            'data/raw/file1.dat': 'hash1',
            'data/raw/file2.dat': 'hash2'
        }

        # Execute
        update_state_with_checksums(state_file, checksums)

        # Verify load was called
        mock_load.assert_called_once_with(state_file)
        
        # Verify save was called with updated state
        assert mock_save.called
        saved_state = mock_save.call_args[0][1]
        
        assert 'artifact_hashes' in saved_state
        assert saved_state['artifact_hashes']['data/raw/file1.dat'] == 'hash1'
        assert saved_state['artifact_hashes']['data/raw/file2.dat'] == 'hash2'
        assert '_metadata' in saved_state['artifact_hashes']

    @patch('checksum_manager.load_state')
    @patch('checksum_manager.save_state')
    def test_update_state_preserves_existing(self, mock_save, mock_load, tmp_path):
        """Test that existing state data is preserved."""
        # Setup mock state with existing data
        initial_state = {
            'project': 'test-project',
            'existing_key': 'existing_value',
            'artifact_hashes': {
                'data/raw/old.dat': 'old_hash'
            }
        }
        mock_load.return_value = initial_state.copy()
        
        state_file = tmp_path / "state.yaml"
        new_checksums = {
            'data/raw/new.dat': 'new_hash'
        }

        # Execute
        update_state_with_checksums(state_file, new_checksums)

        # Verify save was called with updated state
        assert mock_save.called
        saved_state = mock_save.call_args[0][1]
        
        # Check existing data is preserved
        assert saved_state['project'] == 'test-project'
        assert saved_state['existing_key'] == 'existing_value'
        
        # Check both old and new checksums are present
        assert saved_state['artifact_hashes']['data/raw/old.dat'] == 'old_hash'
        assert saved_state['artifact_hashes']['data/raw/new.dat'] == 'new_hash'


class TestValidateExistingChecksums:
    """Tests for the validate_existing_checksums function."""

    @patch('checksum_manager.load_state')
    def test_validate_all_match(self, mock_load, tmp_path):
        """Test validation when all checksums match."""
        # Create test files
        raw_data_dir = tmp_path / "data" / "raw"
        raw_data_dir.mkdir(parents=True)
        
        file1 = raw_data_dir / "file1.dat"
        file1.write_bytes(b"content1")
        
        file2 = raw_data_dir / "file2.dat"
        file2.write_bytes(b"content2")

        # Setup mock state with correct checksums
        state = {
            'artifact_hashes': {
                'data/raw/file1.dat': hashlib.sha256(b"content1").hexdigest(),
                'data/raw/file2.dat': hashlib.sha256(b"content2").hexdigest()
            }
        }
        mock_load.return_value = state

        # Execute
        result = validate_existing_checksums(tmp_path / "state.yaml", raw_data_dir)

        assert result is True

    @patch('checksum_manager.load_state')
    def test_validate_mismatch(self, mock_load, tmp_path):
        """Test validation when checksums don't match."""
        # Create test files
        raw_data_dir = tmp_path / "data" / "raw"
        raw_data_dir.mkdir(parents=True)
        
        file1 = raw_data_dir / "file1.dat"
        file1.write_bytes(b"content1")

        # Setup mock state with incorrect checksum
        state = {
            'artifact_hashes': {
                'data/raw/file1.dat': 'wrong_hash_value'
            }
        }
        mock_load.return_value = state

        # Execute
        result = validate_existing_checksums(tmp_path / "state.yaml", raw_data_dir)

        assert result is False

    @patch('checksum_manager.load_state')
    def test_validate_missing_file(self, mock_load, tmp_path):
        """Test validation when file is missing."""
        # Create empty raw data directory
        raw_data_dir = tmp_path / "data" / "raw"
        raw_data_dir.mkdir(parents=True)

        # Setup mock state referencing missing file
        state = {
            'artifact_hashes': {
                'data/raw/missing.dat': 'some_hash'
            }
        }
        mock_load.return_value = state

        # Execute
        result = validate_existing_checksums(tmp_path / "state.yaml", raw_data_dir)

        assert result is False

    @patch('checksum_manager.load_state')
    def test_validate_no_artifact_hashes(self, mock_load, tmp_path):
        """Test validation when state has no artifact_hashes."""
        raw_data_dir = tmp_path / "data" / "raw"
        raw_data_dir.mkdir(parents=True)
        
        state = {'project': 'test'}
        mock_load.return_value = state

        result = validate_existing_checksums(tmp_path / "state.yaml", raw_data_dir)

        assert result is False