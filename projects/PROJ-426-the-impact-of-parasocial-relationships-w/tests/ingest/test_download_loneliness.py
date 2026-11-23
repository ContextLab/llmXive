"""
Unit tests for download_loneliness.py functionality.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

# Mock the zenodo_get import before importing the module
sys_modules = {}
try:
    import sys
    sys_modules['zenodo_get'] = sys.modules.get('zenodo_get')
    sys.modules['zenodo_get'] = MagicMock()
except Exception:
    pass

from src.ingest.download_loneliness import (
    load_config,
    validate_dataset,
    REQUIRED_COLUMNS,
    LINKABLE_ID_COLS,
    MIN_VALID_ROWS
)

# Restore modules if they existed
if 'zenodo_get' in sys_modules:
    if sys_modules['zenodo_get'] is None:
        del sys.modules['zenodo_get']
    else:
        sys.modules['zenodo_get'] = sys_modules['zenodo_get']

class TestValidateDataset:
    """Tests for the validate_dataset function."""

    def test_missing_linkable_id(self):
        """Should raise ValueError if no linkable ID column exists."""
        df = pd.DataFrame({
            "loneliness_score": [1.0, 2.0, 3.0],
            "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"]
        })
        with pytest.raises(ValueError, match="Data Linkage Impossible"):
            validate_dataset(df, {})

    def test_missing_loneliness_score(self):
        """Should raise ValueError if loneliness_score column is missing."""
        df = pd.DataFrame({
            "username": ["user1", "user2", "user3"],
            "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"]
        })
        with pytest.raises(ValueError, match="Data Linkage Impossible"):
            validate_dataset(df, {})

    def test_insufficient_valid_rows(self):
        """Should raise ValueError if too few rows have non-null loneliness scores."""
        df = pd.DataFrame({
            "username": ["user1", "user2", "user3"],
            "loneliness_score": [None, None, None],
            "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"]
        })
        with pytest.raises(ValueError, match="Data Linkage Impossible"):
            validate_dataset(df, {})

    def test_valid_dataset(self):
        """Should return True for a valid dataset."""
        df = pd.DataFrame({
            "username": ["user1", "user2", "user3"],
            "loneliness_score": [1.0, 2.0, 3.0],
            "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"]
        })
        # Note: MIN_VALID_ROWS is 100, so this will fail the count check in real code.
        # For unit test purposes, we are testing the logic flow.
        # In a real scenario, we would mock the MIN_VALID_ROWS or pass a large enough df.
        # However, since MIN_VALID_ROWS is a constant, we must pass enough rows.
        large_df = pd.DataFrame({
            "username": [f"user{i}" for i in range(101)],
            "loneliness_score": [float(i) for i in range(101)],
            "timestamp": ["2023-01-01" for _ in range(101)]
        })
        result = validate_dataset(large_df, {})
        assert result is True

    def test_missing_timestamp(self):
        """Should raise ValueError if no timestamp column exists."""
        df = pd.DataFrame({
            "username": ["user1", "user2", "user3"],
            "loneliness_score": [1.0, 2.0, 3.0]
        })
        with pytest.raises(ValueError, match="Data Linkage Impossible"):
            validate_dataset(df, {})

class TestLoadConfig:
    """Tests for the load_config function."""

    @patch('src.ingest.download_loneliness.get_config')
    def test_load_config_success(self, mock_get_config):
        """Should return a dictionary with expected keys."""
        mock_get_config.return_value = {
            "data": {"zenodo_loneliness_doi": "10.5281/zenodo.123456"},
            "paths": {
                "raw_loneliness_dataset": "data/raw/loneliness_dataset.parquet",
                "schema": "contracts/unified_dataset.schema.yaml"
            }
        }
        config = load_config()
        assert "zenodo_doi" in config
        assert "output_path" in config
        assert "schema_path" in config

    @patch('src.ingest.download_loneliness.get_config')
    def test_load_config_missing_keys(self, mock_get_config):
        """Should handle missing keys gracefully (using defaults or raising)."""
        mock_get_config.return_value = {}
        # The function currently raises if keys are missing in the nested access
        # depending on how get_config is implemented. We assume it raises or returns None.
        # For this test, we just ensure it doesn't crash unexpectedly on structure.
        with pytest.raises((KeyError, TypeError, Exception)):
            load_config()