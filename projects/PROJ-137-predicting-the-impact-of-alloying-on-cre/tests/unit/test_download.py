"""
Unit tests for src/data/download.py
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import io

from src.data.download import (
    handle_duplicates,
    filter_missing_values,
    create_session_with_backoff
)


class TestHandleDuplicates:
    def test_average_rupture_times(self):
        """Test that duplicate entries are averaged correctly."""
        data = {
            'alloy_id': ['A', 'A', 'A'],
            'temperature': [600, 600, 600],
            'stress': [100, 100, 100],
            'rupture_time': [100.0, 200.0, 300.0],
            'other_val': [1, 2, 3]  # Should be averaged too
        }
        df = pd.DataFrame(data)
        
        result = handle_duplicates(df, key_cols=['alloy_id', 'temperature', 'stress'])
        
        assert len(result) == 1
        assert result['rupture_time'].iloc[0] == 200.0
        assert result['other_val'].iloc[0] == 2.0
        
    def test_no_duplicates(self):
        """Test that unique rows are preserved."""
        data = {
            'alloy_id': ['A', 'B'],
            'temperature': [600, 600],
            'stress': [100, 100],
            'rupture_time': [100.0, 200.0]
        }
        df = pd.DataFrame(data)
        
        result = handle_duplicates(df, key_cols=['alloy_id', 'temperature', 'stress'])
        
        assert len(result) == 2
        
    def test_missing_key_column(self):
        """Test error when key column is missing."""
        df = pd.DataFrame({'a': [1]})
        with pytest.raises(ValueError):
            handle_duplicates(df, key_cols=['missing_col'])


class TestFilterMissingValues:
    def test_filter_nan(self):
        """Test that rows with NaN in required columns are removed."""
        data = {
            'alloy_id': ['A', 'B', 'C'],
            'temperature': [600.0, np.nan, 600.0],
            'stress': [100.0, 100.0, 100.0],
            'rupture_time': [100.0, 200.0, np.nan]
        }
        df = pd.DataFrame(data)
        
        result = filter_missing_values(df, required_cols=['temperature', 'rupture_time'])
        
        assert len(result) == 1
        assert result['alloy_id'].iloc[0] == 'A'
        
    def test_all_required_present(self):
        """Test that rows are kept if all required columns are present."""
        data = {
            'alloy_id': ['A'],
            'temperature': [600.0],
            'stress': [100.0],
            'rupture_time': [100.0]
        }
        df = pd.DataFrame(data)
        
        result = filter_missing_values(df, required_cols=['temperature', 'stress'])
        
        assert len(result) == 1
        
    def test_missing_required_col_in_df(self):
        """Test behavior when a required column is completely missing from DF."""
        df = pd.DataFrame({'a': [1]})
        # Should not crash, just filter based on available columns or warn
        # The implementation logs a warning and filters based on available ones
        # or returns the df if none are available.
        result = filter_missing_values(df, required_cols=['missing'])
        # Since 'missing' is not in df, required_cols becomes empty, returns df
        assert len(result) == 1


class TestSessionCreation:
    def test_session_has_adapter(self):
        """Test that the session has retry adapters mounted."""
        session = create_session_with_backoff()
        assert 'https://' in session.adapters
        assert 'http://' in session.adapters