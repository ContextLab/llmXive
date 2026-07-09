"""
Unit tests for gap filling logic in preprocessing.

Specifically verifies that gaps >= 1 year in GSN data use GSN=0 proxy,
not TSI units, as per FR-002.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import timedelta
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.preprocessing import fill_gaps_gsn


class TestGapFillingLogic:
    """Tests for GSN gap filling behavior."""

    def test_short_gaps_use_interpolation(self):
        """Verify gaps < 1 year are filled via linear interpolation."""
        # Create data with a 6-month gap
        dates = pd.date_range(start='2000-01-01', periods=10, freq='M')
        values = [100.0, 110.0, 120.0, np.nan, np.nan, 150.0, 160.0, 170.0, 180.0, 190.0]
        
        # The gap is 2 months (between index 2 and 5), which is < 1 year
        df = pd.DataFrame({'date': dates, 'gsn': values})
        
        result = fill_gaps_gsn(df, date_col='date', value_col='gsn')
        
        # The NaN values should be interpolated, not set to 0
        # Index 3 should be ~130, Index 4 should be ~140
        assert not result['gsn'].isna().any(), "Short gaps should be interpolated"
        assert result.loc[3, 'gsn'] > 120 and result.loc[3, 'gsn'] < 150
        assert result.loc[4, 'gsn'] > 120 and result.loc[4, 'gsn'] < 150

    def test_long_gaps_use_zero_proxy(self):
        """Verify gaps >= 1 year use GSN=0 proxy, not TSI units."""
        # Create data with a 15-month gap (>= 1 year)
        dates = pd.date_range(start='2000-01-01', periods=8, freq='M')
        # Gap from index 2 to index 6 = 4 months? No, let's make it explicit
        # 2000-01, 2000-02, 2000-03, [gap], 2000-08 (5 months gap is < 1 year)
        # Let's do: 2000-01, 2000-02, 2000-03, [gap 15 months], 2001-06
        dates = pd.to_datetime([
            '2000-01-01', '2000-02-01', '2000-03-01', 
            '2001-06-01', '2001-07-01', '2001-08-01'
        ])
        values = [100.0, 110.0, 120.0, np.nan, np.nan, np.nan, 160.0, 170.0, 180.0]
        
        # Actually, let's construct a simpler case with explicit NaNs
        dates = pd.to_datetime([
            '2000-01-01', '2000-02-01', '2000-03-01', 
            '2001-06-01', '2001-07-01', '2001-08-01'
        ])
        values = [100.0, 110.0, 120.0, np.nan, np.nan, np.nan, 160.0, 170.0, 180.0]
        
        # Reconstruct properly:
        # We need a gap >= 1 year. Let's say:
        # 2000-01-01 (val=100), 2000-02-01 (val=110), 2000-03-01 (val=120)
        # Then gap until 2001-06-01 (val=160) -> gap is ~15 months
        dates = pd.to_datetime([
            '2000-01-01', '2000-02-01', '2000-03-01', 
            '2001-06-01', '2001-07-01', '2001-08-01'
        ])
        # Insert NaNs for the gap period (we don't have data for the gap)
        # The function should detect the time difference between 2000-03-01 and 2001-06-01
        # and fill the gap with 0.
        
        # We need to represent the gap explicitly in the dataframe
        # Let's create a dataframe with the gap dates as NaN
        dates_with_gap = pd.to_datetime([
            '2000-01-01', '2000-02-01', '2000-03-01',
            '2000-04-01', '2000-05-01', '2000-06-01', '2000-07-01', 
            '2000-08-01', '2000-09-01', '2000-10-01', '2000-11-01', 
            '2000-12-01', '2001-01-01', '2001-02-01', '2001-03-01',
            '2001-04-01', '2001-05-01', '2001-06-01', '2001-07-01', '2001-08-01'
        ])
        values_with_gap = [100.0, 110.0, 120.0] + [np.nan] * 14 + [160.0, 170.0, 180.0]
        
        df = pd.DataFrame({'date': dates_with_gap, 'gsn': values_with_gap})
        
        result = fill_gaps_gsn(df, date_col='date', value_col='gsn')
        
        # The gap is from 2000-04-01 to 2001-05-01 (14 months >= 1 year)
        # All these should be filled with 0, not interpolated
        gap_mask = (result['date'] >= '2000-04-01') & (result['date'] <= '2001-05-01')
        gap_values = result.loc[gap_mask, 'gsn']
        
        assert all(gap_values == 0), f"Long gaps should be filled with 0, got values: {gap_values.unique()}"
        
    def test_mixed_gaps_correct_behavior(self):
        """Verify mixed short and long gaps are handled correctly."""
        dates = pd.to_datetime([
            '2000-01-01', '2000-02-01', '2000-03-01',  # valid
            '2000-04-01', '2000-05-01', '2000-06-01',  # 3-month gap (short)
            '2000-07-01', '2000-08-01', '2000-09-01',  # valid
            '2001-09-01', '2001-10-01', '2001-11-01',  # 12-month gap (long)
            '2001-12-01', '2002-01-01', '2002-02-01'   # valid
        ])
        # Create values with NaNs in the gaps
        values = [
            100.0, 110.0, 120.0,  # valid
            np.nan, np.nan, np.nan,  # short gap (3 months)
            150.0, 160.0, 170.0,  # valid
            np.nan, np.nan, np.nan,  # long gap (12 months)
            200.0, 210.0, 220.0   # valid
        ]
        
        df = pd.DataFrame({'date': dates, 'gsn': values})
        result = fill_gaps_gsn(df, date_col='date', value_col='gsn')
        
        # Short gap (2000-04 to 2000-06) should be interpolated
        short_gap_mask = (result['date'] >= '2000-04-01') & (result['date'] <= '2000-06-01')
        short_gap_values = result.loc[short_gap_mask, 'gsn']
        assert all(short_gap_values > 120) and all(short_gap_values < 150), "Short gaps should be interpolated"
        
        # Long gap (2001-09 to 2001-11) should be 0
        long_gap_mask = (result['date'] >= '2001-09-01') & (result['date'] <= '2001-11-01')
        long_gap_values = result.loc[long_gap_mask, 'gsn']
        assert all(long_gap_values == 0), f"Long gaps should be 0, got: {long_gap_values.unique()}"

    def test_no_gaps_unchanged(self):
        """Verify data without gaps remains unchanged."""
        dates = pd.date_range(start='2000-01-01', periods=12, freq='M')
        values = list(range(100, 112))
        
        df = pd.DataFrame({'date': dates, 'gsn': values})
        result = fill_gaps_gsn(df, date_col='date', value_col='gsn')
        
        pd.testing.assert_frame_equal(result, df)

    def test_edge_case_exactly_one_year_gap(self):
        """Verify exactly 1 year gap uses zero proxy."""
        dates = pd.to_datetime([
            '2000-01-01', '2001-01-01'
        ])
        values = [100.0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 200.0]
        
        # Actually, let's make it cleaner:
        # 2000-01-01 (100), then gap until 2001-01-01 (200)
        # We need to represent the gap months
        dates = pd.to_datetime([
            '2000-01-01',
            '2000-02-01', '2000-03-01', '2000-04-01', '2000-05-01', '2000-06-01',
            '2000-07-01', '2000-08-01', '2000-09-01', '2000-10-01', '2000-11-01', '2000-12-01',
            '2001-01-01'
        ])
        values = [100.0] + [np.nan] * 11 + [200.0]
        
        df = pd.DataFrame({'date': dates, 'gsn': values})
        result = fill_gaps_gsn(df, date_col='date', value_col='gsn')
        
        # Gap is 11 months (2000-02 to 2000-12) which is < 1 year? 
        # Wait, the gap is from 2000-01-01 to 2001-01-01, which is 12 months.
        # The function should detect the gap between consecutive non-NaN points.
        # Between 2000-01-01 and 2001-01-01, the gap is 12 months.
        # Since 12 months >= 1 year, it should be filled with 0.
        
        gap_mask = (result['date'] >= '2000-02-01') & (result['date'] <= '2000-12-01')
        gap_values = result.loc[gap_mask, 'gsn']
        
        assert all(gap_values == 0), f"Exactly 1 year gap should be 0, got: {gap_values.unique()}"