"""
Unit tests for save_cleaned_data module.
"""
import pytest
import json
import csv
from pathlib import Path
import sys
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from collect.save_cleaned_data import (
    validate_completeness,
    calculate_checksum,
    REQUIRED_COLUMNS,
    COMPLETENESS_THRESHOLD
)

class TestValidateCompleteness:
    """Tests for validate_completeness function."""

    def test_perfect_completeness(self):
        """Test when all columns are 100% complete."""
        data = [
            {
                'created_at': '2021-01-01',
                'closed_at': '2021-01-02',
                'labels': ['bug'],
                'assignee': 'user1',
                'comments_count': 5,
                'language': 'Python'
            }
        ]
        passed, report = validate_completeness(data, REQUIRED_COLUMNS, 0.95)
        assert passed is True
        assert report['total_rows'] == 1
        assert len(report['failed_columns']) == 0

    def test_partial_completeness_passes(self):
        """Test when completeness is above threshold."""
        # 10 rows, 9 have all fields, 1 missing 'assignee'
        data = [
            {
                'created_at': '2021-01-01',
                'closed_at': '2021-01-02',
                'labels': ['bug'],
                'assignee': 'user1',
                'comments_count': 5,
                'language': 'Python'
            }
        ] * 9 + [
            {
                'created_at': '2021-01-01',
                'closed_at': '2021-01-02',
                'labels': ['bug'],
                'assignee': None,  # Missing
                'comments_count': 5,
                'language': 'Python'
            }
        ]
        
        passed, report = validate_completeness(data, REQUIRED_COLUMNS, 0.90)
        assert passed is True
        # assignee should be 90% complete
        assert report['details']['assignee']['completeness'] == 0.9

    def test_partial_completeness_fails(self):
        """Test when completeness is below threshold."""
        # 10 rows, only 5 have 'assignee'
        data = [
            {
                'created_at': '2021-01-01',
                'closed_at': '2021-01-02',
                'labels': ['bug'],
                'assignee': 'user1',
                'comments_count': 5,
                'language': 'Python'
            }
        ] * 5 + [
            {
                'created_at': '2021-01-01',
                'closed_at': '2021-01-02',
                'labels': ['bug'],
                'assignee': None,  # Missing
                'comments_count': 5,
                'language': 'Python'
            }
        ] * 5
        
        passed, report = validate_completeness(data, REQUIRED_COLUMNS, 0.95)
        assert passed is False
        assert 'assignee' in report['failed_columns']
        assert report['details']['assignee']['completeness'] == 0.5

    def test_empty_dataset(self):
        """Test with empty dataset."""
        passed, report = validate_completeness([], REQUIRED_COLUMNS, 0.95)
        assert passed is False
        assert report['message'] == 'Dataset is empty'

    def test_empty_string_and_empty_list_treated_as_missing(self):
        """Test that empty strings and empty lists are treated as missing."""
        data = [
            {
                'created_at': '',  # Empty string
                'closed_at': '2021-01-02',
                'labels': [],  # Empty list
                'assignee': None,
                'comments_count': 5,
                'language': 'Python'
            }
        ]
        
        passed, report = validate_completeness(data, REQUIRED_COLUMNS, 0.95)
        assert passed is False
        # created_at, labels, assignee should all be 0% complete
        assert report['details']['created_at']['completeness'] == 0.0
        assert report['details']['labels']['completeness'] == 0.0
        assert report['details']['assignee']['completeness'] == 0.0

class TestCalculateChecksum:
    """Tests for calculate_checksum function."""

    def test_same_data_same_checksum(self):
        """Test that identical data produces same checksum."""
        data = [
            {'a': 1, 'b': 2},
            {'c': 3}
        ]
        checksum1 = calculate_checksum(data)
        checksum2 = calculate_checksum(data)
        assert checksum1 == checksum2

    def test_different_data_different_checksum(self):
        """Test that different data produces different checksum."""
        data1 = [{'a': 1}]
        data2 = [{'a': 2}]
        checksum1 = calculate_checksum(data1)
        checksum2 = calculate_checksum(data2)
        assert checksum1 != checksum2

    def test_checksum_is_hex_string(self):
        """Test that checksum is a valid hex string."""
        data = [{'test': 'data'}]
        checksum = calculate_checksum(data)
        assert isinstance(checksum, str)
        assert all(c in '0123456789abcdef' for c in checksum)
        assert len(checksum) == 64  # SHA256 is 64 hex chars