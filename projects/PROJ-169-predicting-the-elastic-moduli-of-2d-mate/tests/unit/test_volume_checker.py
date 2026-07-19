"""
Unit tests for T013e: Volume Checker.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# Import the module under test
# Note: We need to handle the sys.exit behavior carefully in tests
import sys
from io import StringIO

# Import the functions we want to test
# We import the logic functions, not main() directly for unit testing
from code.ingest.volume_checker import count_unique_entries, verify_volume_constraint


class TestCountUniqueEntries:
    def test_empty_dataframe(self, tmp_path):
        """Test handling of an empty parquet file."""
        df = pd.DataFrame(columns=['id', 'node_features'])
        parquet_file = tmp_path / "empty.parquet"
        df.to_parquet(parquet_file)

        count = count_unique_entries(parquet_file)
        assert count == 0

    def test_missing_id_column(self, tmp_path):
        """Test handling of a file without 'id' column."""
        df = pd.DataFrame({'node_features': [[1, 2], [3, 4]]})
        parquet_file = tmp_path / "no_id.parquet"
        df.to_parquet(parquet_file)

        count = count_unique_entries(parquet_file)
        assert count == 0

    def test_duplicate_ids(self, tmp_path):
        """Test that duplicate IDs are counted as one."""
        data = {
            'id': ['mp-1', 'mp-1', 'mp-2', 'mp-3', 'mp-3'],
            'value': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        parquet_file = tmp_path / "dups.parquet"
        df.to_parquet(parquet_file)

        count = count_unique_entries(parquet_file)
        assert count == 3  # mp-1, mp-2, mp-3

    def test_unique_ids(self, tmp_path):
        """Test counting unique IDs."""
        data = {
            'id': [f'mp-{i}' for i in range(10)],
            'value': list(range(10))
        }
        df = pd.DataFrame(data)
        parquet_file = tmp_path / "unique.parquet"
        df.to_parquet(parquet_file)

        count = count_unique_entries(parquet_file)
        assert count == 10

    def test_file_not_found(self, tmp_path):
        """Test handling of a non-existent file."""
        fake_path = tmp_path / "does_not_exist.parquet"
        count = count_unique_entries(fake_path)
        assert count == 0


class TestVerifyVolumeConstraint:
    def test_pass_threshold(self, tmp_path, caplog):
        """Test that verification passes when count >= threshold."""
        data = {
            'id': [f'mp-{i}' for i in range(1000)],
            'value': list(range(1000))
        }
        df = pd.DataFrame(data)
        parquet_file = tmp_path / "pass.parquet"
        df.to_parquet(parquet_file)

        # Should not raise or exit
        result = verify_volume_constraint(parquet_file, threshold=1000)
        assert result is True
        assert "SC-001 Volume Constraint PASSED" in caplog.text

    def test_pass_above_threshold(self, tmp_path, caplog):
        """Test that verification passes when count > threshold."""
        data = {
            'id': [f'mp-{i}' for i in range(1500)],
            'value': list(range(1500))
        }
        df = pd.DataFrame(data)
        parquet_file = tmp_path / "pass_high.parquet"
        df.to_parquet(parquet_file)

        result = verify_volume_constraint(parquet_file, threshold=1000)
        assert result is True

    def test_fail_below_threshold(self, tmp_path, caplog):
        """Test that verification fails and exits when count < threshold."""
        data = {
            'id': [f'mp-{i}' for i in range(500)],
            'value': list(range(500))
        }
        df = pd.DataFrame(data)
        parquet_file = tmp_path / "fail.parquet"
        df.to_parquet(parquet_file)

        # Mock sys.exit to prevent the test from actually exiting
        with patch('code.ingest.volume_checker.sys.exit') as mock_exit:
            result = verify_volume_constraint(parquet_file, threshold=1000)
            mock_exit.assert_called_once_with(1)
            # The function doesn't return if sys.exit is called, but we can check the log
            assert "SC-001 Violation" in caplog.text