"""
Unit tests for save_cleaned_data module.
"""

import json
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime, timezone
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from collect.save_cleaned_data import (
    load_preprocessed_issues,
    calculate_checksum,
    validate_completeness,
    save_metadata
)


class TestCalculateChecksum:
    def test_checksum_deterministic(self):
        """Test that checksum is deterministic for same data."""
        data = [{'id': 1, 'name': 'test'}, {'id': 2, 'name': 'test2'}]
        checksum1 = calculate_checksum(data)
        checksum2 = calculate_checksum(data)
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA256 hex length

    def test_checksum_different_data(self):
        """Test that different data produces different checksums."""
        data1 = [{'id': 1}]
        data2 = [{'id': 2}]
        assert calculate_checksum(data1) != calculate_checksum(data2)

    def test_checksum_empty_list(self):
        """Test checksum for empty list."""
        checksum = calculate_checksum([])
        assert checksum == hashlib.sha256(b'[]').hexdigest()


class TestValidateCompleteness:
    def test_full_completeness(self):
        """Test validation when all columns are fully populated."""
        data = [
            {'created_at': '2023-01-01', 'closed_at': '2023-01-02', 'labels': 'bug', 'assignee': 'user1', 'comments_count': 5},
            {'created_at': '2023-01-01', 'closed_at': '2023-01-02', 'labels': 'feat', 'assignee': 'user2', 'comments_count': 3}
        ]
        required = ['created_at', 'closed_at', 'labels', 'assignee', 'comments_count']
        passed, details = validate_completeness(data, required, threshold=0.95)

        assert passed is True
        assert details['overall_passed'] is True
        assert len(details['failed_columns']) == 0
        for col in required:
            assert details['completeness'][col]['ratio'] == 1.0

    def test_partial_completeness(self):
        """Test validation when some columns have missing values."""
        data = [
            {'created_at': '2023-01-01', 'closed_at': '2023-01-02', 'labels': 'bug', 'assignee': 'user1', 'comments_count': 5},
            {'created_at': '2023-01-01', 'closed_at': None, 'labels': 'feat', 'assignee': None, 'comments_count': 3},
            {'created_at': '2023-01-01', 'closed_at': '2023-01-02', 'labels': None, 'assignee': 'user3', 'comments_count': 1}
        ]
        required = ['created_at', 'closed_at', 'labels', 'assignee', 'comments_count']
        passed, details = validate_completeness(data, required, threshold=0.95)

        # created_at: 3/3 = 100% (pass)
        # closed_at: 2/3 = 66.7% (fail)
        # labels: 2/3 = 66.7% (fail)
        # assignee: 2/3 = 66.7% (fail)
        # comments_count: 3/3 = 100% (pass)
        assert passed is False
        assert len(details['failed_columns']) == 3
        assert 'closed_at' in details['failed_columns']
        assert 'labels' in details['failed_columns']
        assert 'assignee' in details['failed_columns']

    def test_empty_data(self):
        """Test validation with empty dataset."""
        data = []
        required = ['created_at', 'closed_at']
        passed, details = validate_completeness(data, required, threshold=0.95)

        assert passed is False
        assert 'error' in details

    def test_threshold_adjustment(self):
        """Test that changing threshold affects pass/fail."""
        data = [
            {'created_at': '2023-01-01', 'closed_at': None},
            {'created_at': '2023-01-01', 'closed_at': '2023-01-02'}
        ]
        required = ['closed_at']

        # With 50% threshold, should pass
        passed_low, _ = validate_completeness(data, required, threshold=0.5)
        assert passed_low is True

        # With 95% threshold, should fail
        passed_high, _ = validate_completeness(data, required, threshold=0.95)
        assert passed_high is False

    def test_empty_string_treated_as_missing(self):
        """Test that empty strings are treated as missing values."""
        data = [
            {'created_at': '2023-01-01', 'closed_at': ''},
            {'created_at': '2023-01-01', 'closed_at': '2023-01-02'}
        ]
        required = ['closed_at']
        passed, details = validate_completeness(data, required, threshold=0.95)

        assert passed is False
        assert details['completeness']['closed_at']['ratio'] == 0.5


class TestSaveMetadata:
    def test_metadata_structure(self):
        """Test that metadata has correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test.csv'
            checksum = 'abc123'
            validation_results = {'overall_passed': True}
            row_count = 100

            save_metadata(output_path, checksum, validation_results, row_count)

            metadata_path = Path(tmpdir) / 'test_metadata.json'
            assert metadata_path.exists()

            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            assert 'saved_at' in metadata
            assert 'row_count' in metadata
            assert 'checksum_sha256' in metadata
            assert 'completeness_validation' in metadata
            assert metadata['row_count'] == 100
            assert metadata['checksum_sha256'] == checksum

    def test_metadata_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test.csv'
            save_metadata(output_path, 'test', {}, 10)

            metadata_path = Path(tmpdir) / 'test_metadata.json'
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            # Should be parseable as ISO format
            datetime.fromisoformat(metadata['saved_at'])