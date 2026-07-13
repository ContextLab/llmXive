"""
Unit tests for save_cleaned_data.py functionality.
Tests completeness validation, checksum calculation, and metadata saving.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Import the module functions to test
from code.collect.save_cleaned_data import (
    validate_completeness,
    calculate_checksum,
    save_metadata,
    CRITICAL_FIELDS,
    COMPLETENESS_THRESHOLD
)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'repo_name': ['repo1', 'repo2', 'repo3', 'repo4', 'repo5'],
        'issue_number': [1, 2, 3, 4, 5],
        'created_at': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'],
        'closed_at': ['2023-01-02', '2023-01-04', '2023-01-05', '2023-01-06', '2023-01-07'],
        'resolution_time_hours': [24.0, 48.0, 52.0, 26.0, 24.0],
        'author': ['user1', 'user2', 'user3', 'user4', 'user5'],
        'state': ['closed', 'closed', 'closed', 'closed', 'closed']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_dataframe_with_missing():
    """Create a sample DataFrame with some missing values."""
    data = {
        'repo_name': ['repo1', 'repo2', None, 'repo4', 'repo5'],
        'issue_number': [1, 2, 3, None, 5],
        'created_at': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', None],
        'closed_at': ['2023-01-02', '2023-01-04', '2023-01-05', '2023-01-06', '2023-01-07'],
        'resolution_time_hours': [24.0, 48.0, 52.0, 26.0, 24.0],
        'author': ['user1', 'user2', 'user3', 'user4', 'user5'],
        'state': ['closed', 'closed', 'closed', 'closed', 'closed']
    }
    return pd.DataFrame(data)

def test_validate_completeness_perfect(sample_dataframe):
    """Test validation with 100% completeness."""
    is_valid, completeness = validate_completeness(sample_dataframe, COMPLETENESS_THRESHOLD)

    assert is_valid is True
    assert len(completeness) == len(CRITICAL_FIELDS)
    for field, comp in completeness.items():
        assert comp == 1.0

def test_validate_completeness_below_threshold(sample_dataframe_with_missing):
    """Test validation when completeness is below threshold."""
    # With 1 missing out of 5 rows in 3 fields, completeness is 80%
    # which is below 95% threshold
    is_valid, completeness = validate_completeness(sample_dataframe_with_missing, COMPLETENESS_THRESHOLD)

    # Check that at least one field is below threshold
    below_threshold = [comp for comp in completeness.values() if comp < COMPLETENESS_THRESHOLD]
    assert len(below_threshold) > 0
    assert is_valid is False

def test_validate_completeness_empty_dataframe():
    """Test validation with empty DataFrame."""
    df = pd.DataFrame(columns=CRITICAL_FIELDS)
    is_valid, completeness = validate_completeness(df, COMPLETENESS_THRESHOLD)

    assert is_valid is False
    assert len(completeness) == 0

def test_validate_completeness_missing_field(sample_dataframe):
    """Test validation when a critical field is missing."""
    df = sample_dataframe.drop(columns=['repo_name'])
    is_valid, completeness = validate_completeness(df, COMPLETENESS_THRESHOLD)

    assert completeness.get('repo_name', -1) == 0.0
    # Overall completeness will be lower, but might still pass depending on other fields
    # We just check that the missing field is reported as 0.0

def test_calculate_checksum():
    """Test checksum calculation and file writing."""
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test.csv'
        checksum = calculate_checksum(df, output_path)

        # Check that file was created
        assert output_path.exists()

        # Check that checksum is a valid hex string
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)

        # Verify checksum by recalculating
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(output_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        expected_checksum = sha256_hash.hexdigest()

        assert checksum == expected_checksum

def test_save_metadata():
    """Test metadata saving functionality."""
    checksum = "abc123def456"
    completeness = {'field1': 0.95, 'field2': 1.0}

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test.csv'
        output_path.touch()  # Create dummy file

        metadata_path = Path(tmpdir) / 'test_metadata.json'

        save_metadata(checksum, completeness, output_path)

        assert metadata_path.exists()

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        assert metadata['checksum'] == checksum
        assert metadata['completeness_by_field'] == completeness
        assert 'generated_at' in metadata
        assert 'row_count' in metadata
        assert 'schema_version' in metadata