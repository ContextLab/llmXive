"""
Unit tests for outcome type detection in code/analysis.py.
"""

import pytest
import pandas as pd
import numpy as np

# Import the function under test
# Note: We assume the module is in the code directory relative to tests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis import detect_outcome_type


class TestOutcomeTypeDetection:
    """Tests for the detect_outcome_type function."""

    def test_detect_binary_0_1(self):
        """Test detection of binary data with values 0 and 1."""
        df = pd.DataFrame({
            "outcome": [0, 1, 0, 1, 0, 1, 0, 1]
        })
        result = detect_outcome_type(df, "outcome")
        assert result == "binary"

    def test_detect_binary_float_0_1(self):
        """Test detection of binary data with float values 0.0 and 1.0."""
        df = pd.DataFrame({
            "outcome": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
        })
        result = detect_outcome_type(df, "outcome")
        assert result == "binary"

    def test_detect_continuous_various(self):
        """Test detection of continuous data with various values."""
        df = pd.DataFrame({
            "outcome": [0.5, 1.2, 3.4, 5.6, 7.8, 9.0]
        })
        result = detect_outcome_type(df, "outcome")
        assert result == "continuous"

    def test_detect_continuous_integers_not_0_1(self):
        """Test detection when unique values are integers but not 0 and 1 (e.g. 1, 2, 3)."""
        df = pd.DataFrame({
            "outcome": [1, 2, 3, 4, 5]
        })
        result = detect_outcome_type(df, "outcome")
        assert result == "continuous"

    def test_detect_with_nulls(self):
        """Test detection when some values are NaN."""
        df = pd.DataFrame({
            "outcome": [0, 1, np.nan, 1, 0, np.nan]
        })
        result = detect_outcome_type(df, "outcome")
        assert result == "binary"

    def test_detect_all_nulls(self):
        """Test detection when all values are NaN (should default to continuous)."""
        df = pd.DataFrame({
            "outcome": [np.nan, np.nan, np.nan]
        })
        result = detect_outcome_type(df, "outcome")
        assert result == "continuous"

    def test_missing_column(self):
        """Test that ValueError is raised for missing column."""
        df = pd.DataFrame({
            "other_col": [0, 1, 2]
        })
        with pytest.raises(ValueError):
            detect_outcome_type(df, "non_existent_col")

    def test_non_numeric_column(self):
        """Test that ValueError is raised for non-numeric column."""
        df = pd.DataFrame({
            "outcome": ["yes", "no", "yes"]
        })
        with pytest.raises(ValueError):
            detect_outcome_type(df, "outcome")

    def test_single_unique_value(self):
        """Test detection when only one unique value exists (e.g., all 0s)."""
        df = pd.DataFrame({
            "outcome": [0, 0, 0, 0]
        })
        # Should be continuous because it's not exactly {0, 1}
        result = detect_outcome_type(df, "outcome")
        assert result == "continuous"

    def test_binary_with_zeros_only(self):
        """Test detection when only 0s are present (structural zeros)."""
        df = pd.DataFrame({
            "outcome": [0, 0, 0, 0]
        })
        # Since unique set is {0}, not {0, 1}, it's continuous
        result = detect_outcome_type(df, "outcome")
        assert result == "continuous"