"""
Unit tests for subject filtering logic in download_hcp.py.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download_hcp import filter_subjects

class TestFilterSubjects:
    def test_filter_valid_sleep_and_fd(self):
        """Test that subjects with valid sleep and low FD are kept."""
        data = {
            "Subject": ["100101", "100307", "100406"],
            "Sleep": [1.0, 2.0, 3.0],
            "MeanFD": [0.1, 0.2, 0.15]
        }
        df = pd.DataFrame(data)
        result = filter_subjects(df)
        assert len(result) == 3
        assert "100101" in result

    def test_filter_invalid_sleep(self):
        """Test that subjects with NaN Sleep are excluded."""
        data = {
            "Subject": ["100101", "100307"],
            "Sleep": [np.nan, 2.0],
            "MeanFD": [0.1, 0.2]
        }
        df = pd.DataFrame(data)
        result = filter_subjects(df)
        assert len(result) == 1
        assert "100101" not in result
        assert "100307" in result

    def test_filter_high_fd(self):
        """Test that subjects with FD > 0.3 are excluded."""
        data = {
            "Subject": ["100101", "100307", "100406"],
            "Sleep": [1.0, 2.0, 3.0],
            "MeanFD": [0.1, 0.4, 0.15]
        }
        df = pd.DataFrame(data)
        result = filter_subjects(df)
        assert len(result) == 2
        assert "100307" not in result
        assert "100101" in result
        assert "100406" in result

    def test_filter_both_invalid(self):
        """Test exclusion when both Sleep and FD are invalid."""
        data = {
            "Subject": ["100101"],
            "Sleep": [np.nan],
            "MeanFD": [0.5]
        }
        df = pd.DataFrame(data)
        result = filter_subjects(df)
        assert len(result) == 0

    def test_missing_fd_column_defaults(self):
        """Test behavior when FD column is missing (should warn and assume 0)."""
        data = {
            "Subject": ["100101"],
            "Sleep": [1.0]
        }
        df = pd.DataFrame(data)
        # This should not raise an error, but log a warning
        result = filter_subjects(df)
        assert len(result) == 1
        assert "100101" in result

    def test_missing_sleep_column_raises(self):
        """Test that missing Sleep column raises ValueError."""
        data = {
            "Subject": ["100101"],
            "MeanFD": [0.1]
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError):
            filter_subjects(df)