"""
Unit tests for the loaders module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from loaders import compute_checksum, scan_for_pii
from config import get_dataset_config

class TestComputeChecksum:
    """Tests for the compute_checksum function."""

    def test_checksum_consistency(self):
        """Test that the same data produces the same checksum."""
        data = {"key": "value", "number": 42}
        checksum1 = compute_checksum(data)
        checksum2 = compute_checksum(data)
        assert checksum1 == checksum2

    def test_checksum_different_data(self):
        """Test that different data produces different checksums."""
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}
        checksum1 = compute_checksum(data1)
        checksum2 = compute_checksum(data2)
        assert checksum1 != checksum2

    def test_checksum_empty_dict(self):
        """Test checksum computation for empty data."""
        data = {}
        checksum = compute_checksum(data)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 produces 64 hex characters

    def test_checksum_list(self):
        """Test checksum computation for list data."""
        data = [1, 2, 3, 4, 5]
        checksum = compute_checksum(data)
        assert isinstance(checksum, str)
        assert len(checksum) == 64

class TestScanForPII:
    """Tests for the scan_for_pii function."""

    def test_no_pii(self):
        """Test detection when no PII is present."""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        flagged = scan_for_pii(df, threshold=10)
        assert len(flagged) == 0

    def test_email_detection(self):
        """Test detection of email addresses."""
        # Create a column with many email addresses
        emails = [f"user{i}@example.com" for i in range(20)]
        df = pd.DataFrame({
            'emails': emails,
            'normal': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        })
        flagged = scan_for_pii(df, threshold=10)
        assert 'emails' in flagged

    def test_ssn_detection(self):
        """Test detection of Social Security Numbers."""
        # Create a column with SSN-like patterns
        ssns = [f"{i:03d}-{i:02d}-{i:04d}" for i in range(20)]
        df = pd.DataFrame({
            'ssns': ssns,
            'normal': list(range(20))
        })
        flagged = scan_for_pii(df, threshold=10)
        assert 'ssns' in flagged

    def test_ip_address_detection(self):
        """Test detection of IP addresses."""
        # Create a column with IP addresses
        ips = [f"192.168.1.{i}" for i in range(20)]
        df = pd.DataFrame({
            'ips': ips,
            'normal': list(range(20))
        })
        flagged = scan_for_pii(df, threshold=10)
        assert 'ips' in flagged

    def test_phone_number_detection(self):
        """Test detection of phone numbers."""
        # Create a column with phone numbers
        phones = [f"123-456-{i:04d}" for i in range(20)]
        df = pd.DataFrame({
            'phones': phones,
            'normal': list(range(20))
        })
        flagged = scan_for_pii(df, threshold=10)
        assert 'phones' in flagged

    def test_threshold_behavior(self):
        """Test that the threshold parameter works correctly."""
        # Create a column with 5 emails (below threshold of 10)
        emails = [f"user{i}@example.com" for i in range(5)]
        df = pd.DataFrame({
            'emails': emails,
            'normal': list(range(5))
        })
        flagged = scan_for_pii(df, threshold=10)
        assert len(flagged) == 0  # Should not flag due to threshold

        # Same data with threshold of 5
        flagged = scan_for_pii(df, threshold=5)
        assert 'emails' in flagged  # Should flag now

class TestDatasetConfig:
    """Tests for the dataset configuration."""

    def test_config_exists(self):
        """Test that the dataset configuration can be retrieved."""
        config = get_dataset_config()
        assert isinstance(config, list)
        assert len(config) > 0

    def test_config_structure(self):
        """Test that each dataset entry has required fields."""
        config = get_dataset_config()
        required_fields = {'id', 'outcome_type'}

        for entry in config:
            assert isinstance(entry, dict)
            assert required_fields.issubset(entry.keys())

    def test_dataset_distribution(self):
        """Test that the dataset distribution matches the specification."""
        config = get_dataset_config()

        continuous_count = sum(1 for d in config if d['outcome_type'] == 'continuous')
        count_count = sum(1 for d in config if d['outcome_type'] == 'count')
        binary_count = sum(1 for d in config if d['outcome_type'] == 'binary')

        # According to T004a: 3 continuous, 3 count, 4 binary
        assert continuous_count == 3, f"Expected 3 continuous datasets, found {continuous_count}"
        assert count_count == 3, f"Expected 3 count datasets, found {count_count}"
        assert binary_count == 4, f"Expected 4 binary datasets, found {binary_count}"

    def test_specific_dataset_ids(self):
        """Test that the specific dataset IDs from T004a are present."""
        config = get_dataset_config()
        dataset_ids = [d['id'] for d in config]

        # Continuous datasets
        assert 'iris' in dataset_ids
        assert 'wine' in dataset_ids
        assert 'wine_quality_red' in dataset_ids

        # Count datasets
        assert 'concrete' in dataset_ids
        assert 'airfoil' in dataset_ids
        assert 'yacht' in dataset_ids

        # Binary datasets
        assert 'breast_cancer' in dataset_ids
        assert 'heart_disease' in dataset_ids
        assert 'pima' in dataset_ids
        assert 'ionosphere' in dataset_ids
