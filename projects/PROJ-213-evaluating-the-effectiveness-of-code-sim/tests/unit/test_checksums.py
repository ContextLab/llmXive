#!/usr/bin/env python3
"""
Unit tests for checksum generation functionality (T001a).

Tests the code/checksums.py module per Constitution Principle III.
"""

import json
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

# Import the module under test
from code.checksums import compute_file_checksums, generate_checksums_for_dataset, write_checksums_to_map


class TestComputeFileChecksums:
    """Tests for the compute_file_checksums function."""

    def test_compute_checksums_creates_valid_hashes(self, tmp_path):
        """Verify checksums are valid hex strings of correct length."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        checksums = compute_file_checksums(test_file)
        
        assert 'md5' in checksums
        assert 'sha256' in checksums
        assert len(checksums['md5']) == 32  # MD5 is 32 hex chars
        assert len(checksums['sha256']) == 64  # SHA256 is 64 hex chars
        
        # Verify they are valid hex
        int(checksums['md5'], 16)
        int(checksums['sha256'], 16)

    def test_compute_checksums_deterministic(self, tmp_path):
        """Verify same file produces same checksums on repeated runs."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Deterministic test content")
        
        checksums1 = compute_file_checksums(test_file)
        checksums2 = compute_file_checksums(test_file)
        
        assert checksums1['md5'] == checksums2['md5']
        assert checksums1['sha256'] == checksums2['sha256']

    def test_compute_checksums_different_content_different_hashes(self, tmp_path):
        """Verify different content produces different checksums."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        
        file1.write_text("Content A")
        file2.write_text("Content B")
        
        checksums1 = compute_file_checksums(file1)
        checksums2 = compute_file_checksums(file2)
        
        assert checksums1['md5'] != checksums2['md5']
        assert checksums1['sha256'] != checksums2['sha256']


class TestGenerateChecksumsForDataset:
    """Tests for the generate_checksums_for_dataset function."""

    def test_generates_checksums_for_all_files(self, tmp_path):
        """Verify all files in directory get checksums."""
        # Create test files
        (tmp_path / "file1.txt").write_text("Content 1")
        (tmp_path / "file2.txt").write_text("Content 2")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("Content 3")
        
        checksums = generate_checksums_for_dataset(str(tmp_path))
        
        assert len(checksums) == 3
        file_paths = [c['file_path'] for c in checksums]
        assert "file1.txt" in file_paths
        assert "file2.txt" in file_paths
        assert "subdir/file3.txt" in file_paths

    def test_checksum_entry_has_required_fields(self, tmp_path):
        """Verify checksum entries have all required fields per spec."""
        (tmp_path / "test.txt").write_text("Test content")
        
        checksums = generate_checksums_for_dataset(str(tmp_path))
        entry = checksums[0]
        
        # Required fields per T001a spec
        required_fields = ['artifact_id', 'file_path', 'checksum', 'timestamp', 'hash', 'artifact_type']
        for field in required_fields:
            assert field in entry, f"Missing required field: {field}"

    def test_timestamp_is_iso8601(self, tmp_path):
        """Verify timestamp field is ISO8601 format."""
        (tmp_path / "test.txt").write_text("Test")
        
        checksums = generate_checksums_for_dataset(str(tmp_path))
        entry = checksums[0]
        
        # Should be parseable as ISO8601
        timestamp = entry['timestamp']
        assert timestamp.endswith('Z') or '+' in timestamp or timestamp.endswith('+00:00')

    def test_raises_on_missing_directory(self):
        """Verify FileNotFoundError is raised for non-existent directory."""
        with pytest.raises(FileNotFoundError):
            generate_checksums_for_dataset('/nonexistent/path/that/does/not/exist')


class TestWriteChecksumsToMap:
    """Tests for the write_checksums_to_map function."""

    def test_creates_output_file(self, tmp_path):
        """Verify function creates the output JSON file."""
        output_path = tmp_path / "state" / "map.json"
        
        checksums = [
            {
                'artifact_id': 'test_artifact',
                'file_path': 'test.txt',
                'checksum': 'abc123',
                'timestamp': '2024-01-01T00:00:00Z',
                'hash': 'sha256',
                'artifact_type': 'dataset_file',
                'md5': 'def456'
            }
        ]
        
        write_checksums_to_map(checksums, str(output_path))
        
        assert output_path.exists()

    def test_output_json_is_valid(self, tmp_path):
        """Verify output file contains valid JSON."""
        output_path = tmp_path / "state" / "map.json"
        
        checksums = [
            {
                'artifact_id': 'test_artifact',
                'file_path': 'test.txt',
                'checksum': 'abc123',
                'timestamp': '2024-01-01T00:00:00Z',
                'hash': 'sha256',
                'artifact_type': 'dataset_file',
                'md5': 'def456'
            }
        ]
        
        write_checksums_to_map(checksums, str(output_path))
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert 'humaneval_checksums' in data
        assert len(data['humaneval_checksums']) == 1

    def test_preserves_existing_map(self, tmp_path):
        """Verify function preserves existing map content when updating."""
        output_path = tmp_path / "state" / "map.json"
        
        # Create existing map
        output_path.parent.mkdir(parents=True)
        existing_data = {'existing_key': 'existing_value'}
        with open(output_path, 'w') as f:
            json.dump(existing_data, f)
        
        checksums = [
            {
                'artifact_id': 'test_artifact',
                'file_path': 'test.txt',
                'checksum': 'abc123',
                'timestamp': '2024-01-01T00:00:00Z',
                'hash': 'sha256',
                'artifact_type': 'dataset_file',
                'md5': 'def456'
            }
        ]
        
        write_checksums_to_map(checksums, str(output_path))
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['existing_key'] == 'existing_value'
        assert 'humaneval_checksums' in data


class TestConstitutionalCompliance:
    """Tests for Constitution Principle III compliance."""

    def test_checksums_use_sha256_as_primary(self, tmp_path):
        """Verify SHA256 is used as the primary checksum per Principle III."""
        (tmp_path / "test.txt").write_text("Test")
        
        checksums = generate_checksums_for_dataset(str(tmp_path))
        entry = checksums[0]
        
        assert entry['hash'] == 'sha256'
        assert len(entry['checksum']) == 64  # SHA256 length

    def test_checksums_record_timestamp(self, tmp_path):
        """Verify timestamps are recorded for reproducibility."""
        (tmp_path / "test.txt").write_text("Test")
        
        checksums = generate_checksums_for_dataset(str(tmp_path))
        entry = checksums[0]
        
        assert 'timestamp' in entry
        assert entry['timestamp'] is not None

    def test_checksums_have_unique_artifact_ids(self, tmp_path):
        """Verify each file gets a unique artifact_id."""
        (tmp_path / "file1.txt").write_text("Content 1")
        (tmp_path / "file2.txt").write_text("Content 2")
        
        checksums = generate_checksums_for_dataset(str(tmp_path))
        artifact_ids = [c['artifact_id'] for c in checksums]
        
        assert len(artifact_ids) == len(set(artifact_ids))  # All unique