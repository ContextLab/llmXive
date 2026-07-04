"""
Unit tests for T015: Preprocessing filtering logic.

Tests specifically for:
- Exclusion of missing ACE scores.
- Exclusion of poor MRI quality flags.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path for imports if running directly
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.preprocessing import (
    _filter_missing_ace, 
    _filter_mri_quality, 
    ACE_SCORE_COLUMN, 
    MRI_QUALITY_FLAGS
)

class TestFilterMissingACE:
    def test_filter_removes_nan(self):
        """Test that rows with NaN ACE are removed."""
        df = pd.DataFrame({
            ACE_SCORE_COLUMN: [10.0, np.nan, 20.0, np.nan],
            'other': [1, 2, 3, 4]
        })
        result, count = _filter_missing_ace(df)
        assert len(result) == 2
        assert count == 2
        assert not result[ACE_SCORE_COLUMN].isna().any()

    def test_filter_removes_out_of_range(self):
        """Test that rows with ACE outside valid range are removed."""
        df = pd.DataFrame({
            ACE_SCORE_COLUMN: [-5.0, 10.0, 150.0, 50.0], # -5 and 150 invalid
            'other': [1, 2, 3, 4]
        })
        result, count = _filter_missing_ace(df)
        # Assuming valid range is 0-100
        assert len(result) == 2
        assert count == 2
        assert all((result[ACE_SCORE_COLUMN] >= 0) & (result[ACE_SCORE_COLUMN] <= 100))

    def test_missing_column_raises(self):
        """Test that missing ACE column raises ValueError."""
        df = pd.DataFrame({'other': [1, 2, 3]})
        with pytest.raises(ValueError):
            _filter_missing_ace(df)

class TestFilterMRIQuality:
    def test_filter_removes_bad_flags(self):
        """Test that rows with 'bad' or 'fail' flags are removed."""
        df = pd.DataFrame({
            'motion_flag': ['good', 'bad', 'good', 'fail'],
            'other': [1, 2, 3, 4]
        })
        result, count = _filter_mri_quality(df)
        assert len(result) == 2
        assert count == 2
        # Check remaining rows
        assert all(result['motion_flag'].isin(['good']))

    def test_filter_removes_numeric_bad_flags(self):
        """Test that rows with numeric 1 (if treated as bad) are removed."""
        # Assuming 1 is bad based on 'bad_values' set containing '1'
        df = pd.DataFrame({
            'quality_control_flag': [0, 1, 0, 1],
            'other': [1, 2, 3, 4]
        })
        result, count = _filter_mri_quality(df)
        assert len(result) == 2
        assert count == 2

    def test_no_bad_flags_returns_all(self):
        """Test that if no bad flags exist, all rows are kept."""
        df = pd.DataFrame({
            'motion_flag': ['good', 'good', 'pass'],
            'other': [1, 2, 3]
        })
        result, count = _filter_mri_quality(df)
        assert len(result) == 3
        assert count == 0

    def test_missing_flag_column_ignored(self):
        """Test that missing flag columns are ignored gracefully."""
        df = pd.DataFrame({
            'other': [1, 2, 3]
        })
        result, count = _filter_mri_quality(df)
        assert len(result) == 3
        assert count == 0
