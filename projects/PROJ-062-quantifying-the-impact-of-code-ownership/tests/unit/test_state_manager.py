"""
Unit tests for state_manager.py
"""

import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.state_manager import (
    calculate_file_hash,
    generate_state_snapshot,
    save_state_snapshot,
    verify_file_integrity,
    verify_state_snapshot,
    OWNERSHIP_METRICS_DIR,
    STATE_DIR,
    PROJECT_ROOT
)


class TestCalculateFileHash:
    """Tests for calculate_file_hash function"""

    def test_hash_consistency(self, tmp_path):
        """Test that same file produces same hash"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        hash1 = calculate_file_hash(test_file)
        hash2 = calculate_file_hash(test_file)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_hash_content_change(self, tmp_path):
        """Test that different content produces different hash"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content A")

        hash1 = calculate_file_hash(test_file)
        test_file.write_text("Content B")
        hash2 = calculate_file_hash(test_file)

        assert hash1 != hash2

    def test_file_not_found(self, tmp_path):
        """Test that missing file raises FileNotFoundError"""
        missing_file = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            calculate_file_hash(missing_file)


class TestVerifyFileIntegrity:
    """Tests for verify_file_integrity function"""

    def test_valid_integrity(self, tmp_path):
        """Test verification with matching hash"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        file_hash = calculate_file_hash(test_file)
        result = verify_file_integrity(test_file, file_hash)

        assert result is True

    def test_invalid_integrity(self, tmp_path):
        """Test verification with mismatched hash"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        wrong_hash = "a" * 64
        result = verify_file_integrity(test_file, wrong_hash)

        assert result is False

    def test_missing_file(self, tmp_path):
        """Test verification with missing file"""
        missing_file = tmp_path / "nonexistent.txt"
        dummy_hash = "a" * 64

        result = verify_file_integrity(missing_file, dummy_hash)

        assert result is False


class TestGenerateStateSnapshot:
    """Tests for generate_state_snapshot function"""

    def test_empty_snapshot(self, mocker):
        """Test snapshot generation with no CSV files"""
        mocker.patch('code.state_manager.get_ownership_csv_files', return_value=[])

        snapshot = generate_state_snapshot()

        assert snapshot['total_files'] == 0
        assert snapshot['status'] == 'empty'
        assert 'timestamp' in snapshot
        assert 'files' in snapshot

    def test_snapshot_with_files(self, tmp_path, mocker):
        """Test snapshot generation with CSV files"""
        # Create mock CSV files
        csv_file1 = tmp_path / "repo1_ownership.csv"
        csv_file1.write_text("author,file,commits\nAlice,main.py,10")

        csv_file2 = tmp_path / "repo2_ownership.csv"
        csv_file2.write_text("author,file,commits\nBob,utils.py,5")

        mocker.patch('code.state_manager.OWNERSHIP_METRICS_DIR', tmp_path)
        mocker.patch('code.state_manager.get_ownership_csv_files', return_value=[csv_file1, csv_file2])

        snapshot = generate_state_snapshot()

        assert snapshot['total_files'] == 2
        assert snapshot['status'] == 'complete'
        assert len(snapshot['files']) == 2

        # Check file entries
        for file_entry in snapshot['files']:
            assert 'filename' in file_entry
            assert 'hash' in file_entry
            assert 'size_bytes' in file_entry
            assert 'last_modified' in file_entry


class TestSaveStateSnapshot:
    """Tests for save_state_snapshot function"""

    def test_save_and_load(self, tmp_path):
        """Test saving and loading a state snapshot"""
        test_snapshot = {
            'timestamp': '2024-01-01T00:00:00',
            'version': '1.0',
            'files': [],
            'total_files': 0,
            'status': 'empty'
        }

        saved_path = save_state_snapshot(test_snapshot, "test_snapshot.yaml", snapshot_dir=tmp_path)

        assert saved_path.exists()
        assert saved_path.name == "test_snapshot.yaml"

        with open(saved_path, 'r') as f:
            loaded = yaml.safe_load(f)

        assert loaded == test_snapshot

    def test_default_naming(self, tmp_path):
        """Test that default naming uses timestamp"""
        test_snapshot = {'test': 'data'}

        saved_path = save_state_snapshot(test_snapshot, snapshot_dir=tmp_path)

        assert saved_path.exists()
        assert saved_path.name.endswith('.yaml')
        assert saved_path.name.startswith('state_')


class TestVerifyStateSnapshot:
    """Tests for verify_state_snapshot function"""

    def test_verify_valid_snapshot(self, tmp_path):
        """Test verification of a valid snapshot"""
        # Create a test file
        test_file = tmp_path / "test.csv"
        test_file.write_text("test,data")
        file_hash = calculate_file_hash(test_file)

        # Create snapshot
        snapshot_data = {
            'timestamp': '2024-01-01T00:00:00',
            'version': '1.0',
            'files': [{
                'filename': 'test.csv',
                'relative_path': str(test_file.relative_to(tmp_path)),
                'hash': file_hash,
                'size_bytes': test_file.stat().st_size
            }],
            'total_files': 1,
            'status': 'complete'
        }

        snapshot_file = tmp_path / "snapshot.yaml"
        with open(snapshot_file, 'w') as f:
            yaml.dump(snapshot_data, f)

        results = verify_state_snapshot(snapshot_file)

        assert results['status'] == 'complete'
        assert results['files_valid'] == 1
        assert results['files_invalid'] == 0
        assert results['files_missing'] == 0

    def test_verify_missing_file(self, tmp_path):
        """Test verification when file is missing"""
        snapshot_data = {
            'timestamp': '2024-01-01T00:00:00',
            'version': '1.0',
            'files': [{
                'filename': 'missing.csv',
                'relative_path': 'data/missing.csv',
                'hash': 'a' * 64
            }],
            'total_files': 1,
            'status': 'complete'
        }

        snapshot_file = tmp_path / "snapshot.yaml"
        with open(snapshot_file, 'w') as f:
            yaml.dump(snapshot_data, f)

        results = verify_state_snapshot(snapshot_file)

        assert results['files_missing'] == 1
        assert results['files_valid'] == 0

    def test_verify_invalid_hash(self, tmp_path):
        """Test verification when hash doesn't match"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("test,data")

        snapshot_data = {
            'timestamp': '2024-01-01T00:00:00',
            'version': '1.0',
            'files': [{
                'filename': 'test.csv',
                'relative_path': str(test_file),
                'hash': 'a' * 64  # Wrong hash
            }],
            'total_files': 1,
            'status': 'complete'
        }

        snapshot_file = tmp_path / "snapshot.yaml"
        with open(snapshot_file, 'w') as f:
            yaml.dump(snapshot_data, f)

        results = verify_state_snapshot(snapshot_file)

        assert results['files_invalid'] == 1
        assert results['files_valid'] == 0