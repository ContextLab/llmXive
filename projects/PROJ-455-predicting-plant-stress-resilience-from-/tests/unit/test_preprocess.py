"""
Unit tests for preprocessing functions.
"""

import pytest
import pandas as pd
import numpy as np

from data.preprocess import check_missing_threshold
from utils.logging import DataRejectionError


class TestCheckMissingThreshold:
    """Tests for the check_missing_threshold function."""
    
    def test_no_missing_values(self):
        """Test that a DataFrame with no missing values passes."""
        df = pd.DataFrame({
            'A': [1.0, 2.0, 3.0],
            'B': [4.0, 5.0, 6.0]
        })
        # Should not raise
        check_missing_threshold(df, threshold=0.1)
        
    def test_below_threshold(self):
        """Test that a DataFrame with missing values below threshold passes."""
        # 1 missing out of 12 cells = 8.33% < 10%
        df = pd.DataFrame({
            'A': [1.0, 2.0, np.nan, 4.0],
            'B': [4.0, 5.0, 6.0, 7.0],
            'C': [8.0, 9.0, 10.0, 11.0]
        })
        # Should not raise
        check_missing_threshold(df, threshold=0.1)
        
    def test_exactly_at_threshold(self):
        """Test that a DataFrame with missing values exactly at threshold passes."""
        # 3 missing out of 30 cells = 10%
        df = pd.DataFrame({
            'A': [np.nan, np.nan, np.nan] + [1.0] * 7,
            'B': [1.0] * 10,
            'C': [1.0] * 10
        })
        # Should not raise
        check_missing_threshold(df, threshold=0.1)
        
    def test_above_threshold_overall(self):
        """Test that a DataFrame with overall missing > threshold raises error."""
        # 4 missing out of 12 cells = 33.33% > 10%
        df = pd.DataFrame({
            'A': [np.nan, np.nan, np.nan, np.nan],
            'B': [1.0, 2.0, 3.0, 4.0],
            'C': [5.0, 6.0, 7.0, 8.0]
        })
        with pytest.raises(DataRejectionError) as exc_info:
            check_missing_threshold(df, threshold=0.1)
        assert "exceeds threshold" in str(exc_info.value)
        
    def test_above_threshold_column(self):
        """Test that a DataFrame with a column exceeding threshold raises error."""
        # Column A has 50% missing (2 out of 4), which is > 10%
        df = pd.DataFrame({
            'A': [np.nan, np.nan, 1.0, 2.0],
            'B': [1.0, 2.0, 3.0, 4.0],
            'C': [5.0, 6.0, 7.0, 8.0]
        })
        with pytest.raises(DataRejectionError) as exc_info:
            check_missing_threshold(df, threshold=0.1)
        assert "exceeds threshold" in str(exc_info.value)
        assert "A" in str(exc_info.value)
        
    def test_empty_dataframe(self):
        """Test that an empty DataFrame does not raise an error."""
        df = pd.DataFrame()
        # Should not raise, just log a warning
        check_missing_threshold(df, threshold=0.1)
        
    def test_single_column_all_missing(self):
        """Test a single column DataFrame with all missing values."""
        df = pd.DataFrame({
            'A': [np.nan, np.nan, np.nan]
        })
        with pytest.raises(DataRejectionError):
            check_missing_threshold(df, threshold=0.1)
            
    def test_custom_threshold(self):
        """Test with a custom threshold."""
        # 20% missing overall
        df = pd.DataFrame({
            'A': [np.nan, np.nan, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
            'B': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        })
        # 2/20 = 10% missing, should pass with 0.1 threshold
        check_missing_threshold(df, threshold=0.1)
        # Should fail with 0.05 threshold (5%)
        with pytest.raises(DataRejectionError):
            check_missing_threshold(df, threshold=0.05)