"""
Unit tests for station exclusion logic regarding missing data gaps.

Specifically tests the logic in src.data.preprocessing::find_max_contiguous_gap
and src.data.preprocessing::filter_stations to ensure stations with >30 day 
contiguous gaps are excluded.
"""
import pandas as pd
import numpy as np
import pytest
from datetime import timedelta
from pathlib import Path
import sys
import os

# Ensure src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.preprocessing import find_max_contiguous_gap, filter_stations, calculate_missing_ratio


class TestStationExclusionGaps:
    """Tests for verifying station exclusion based on contiguous missing gaps."""

    def _create_station_df(self, dates, values, station_id="STN001"):
        """Helper to create a DataFrame with specific dates and values."""
        df = pd.DataFrame({
            "station_id": station_id,
            "date": dates,
            "tmax": values
        })
        return df

    def test_no_gap_exclusion(self):
        """Station with no gaps should be kept."""
        dates = pd.date_range("2000-01-01", periods=365, freq="D")
        values = np.random.randn(365)
        df = self._create_station_df(dates, values)
        
        max_gap = find_max_contiguous_gap(df)
        assert max_gap == 0, "No gap should exist."
        
        filtered = filter_stations({"STN001": df}, max_gap_threshold=30, missing_ratio_threshold=0.15)
        assert "STN001" in filtered, "Station with no gaps should be included."

    def test_30_day_gap_exclusion_boundary(self):
        """Station with exactly 30 day gap should be kept (threshold is >30)."""
        # Create a sequence with a 30-day gap
        start_dates = pd.date_range("2000-01-01", periods=30, freq="D")
        end_dates = pd.date_range("2000-02-02", periods=30, freq="D") # Gap of 30 days (Jan 31 to Feb 1 is 1 day, gap is 30 days if we skip 30 days)
        
        # Let's construct explicit dates to ensure a 30-day gap
        # Jan 1 to Jan 30 (30 days)
        # Skip Jan 31, Feb 1, ..., Feb 30 (30 days missing)
        # Feb 31? No. Let's do: Jan 1 - Jan 30, then skip 30 days, then Feb 29 (if leap) or Mar 1.
        
        dates_part1 = pd.date_range("2000-01-01", periods=30, freq="D")
        # 30 missing days: Jan 31 to Feb 29 (2000 is leap) -> 30 days
        # Next date: Mar 1
        dates_part2 = pd.date_range("2000-03-01", periods=30, freq="D")
        
        all_dates = dates_part1.append(dates_part2)
        values = np.ones(len(all_dates))
        
        df = self._create_station_df(all_dates, values)
        
        max_gap = find_max_contiguous_gap(df)
        # The gap is from Jan 31 to Feb 29 inclusive = 30 days
        assert max_gap == 30, f"Gap should be exactly 30 days, got {max_gap}"
        
        # Threshold is > 30, so 30 should pass
        filtered = filter_stations({"STN001": df}, max_gap_threshold=30, missing_ratio_threshold=0.15)
        assert "STN001" in filtered, "Station with exactly 30 day gap should be included."

    def test_31_day_gap_exclusion(self):
        """Station with 31 day gap should be excluded."""
        # Create a sequence with a 31-day gap
        dates_part1 = pd.date_range("2000-01-01", periods=30, freq="D")
        # 31 missing days: Jan 31 to Feb 29 (30 days) + Mar 1 (1 day) = 31 days?
        # Let's just skip 31 days explicitly.
        # Jan 1 to Jan 30 (30 days)
        # Skip 31 days: Jan 31 to Feb 29 (2000 is leap year, 29 days) + Mar 1 (1 day) = 30 days?
        # 2000 is a leap year. Jan has 31 days.
        # Part 1: Jan 1 - Jan 30 (30 days)
        # Missing: Jan 31, Feb 1 - Feb 29 (29 days) -> Total 30 days missing.
        # We need 31.
        # Let's skip 31 days starting Jan 31.
        # Jan 31 to Feb 29 = 30 days. Mar 1 is the 31st missing day.
        # Next date: Mar 2.
        
        dates_part1 = pd.date_range("2000-01-01", periods=30, freq="D")
        dates_part2 = pd.date_range("2000-03-02", periods=30, freq="D")
        
        all_dates = dates_part1.append(dates_part2)
        values = np.ones(len(all_dates))
        
        df = self._create_station_df(all_dates, values)
        
        max_gap = find_max_contiguous_gap(df)
        assert max_gap == 31, f"Gap should be exactly 31 days, got {max_gap}"
        
        # Threshold is > 30, so 31 should fail
        filtered = filter_stations({"STN001": df}, max_gap_threshold=30, missing_ratio_threshold=0.15)
        assert "STN001" not in filtered, "Station with 31 day gap should be excluded."

    def test_large_gap_exclusion(self):
        """Station with a very large gap (e.g., 100 days) should be excluded."""
        dates_part1 = pd.date_range("2000-01-01", periods=10, freq="D")
        dates_part2 = pd.date_range("2000-05-01", periods=10, freq="D") # ~100 day gap
        
        all_dates = dates_part1.append(dates_part2)
        values = np.ones(len(all_dates))
        
        df = self._create_station_df(all_dates, values)
        
        max_gap = find_max_contiguous_gap(df)
        assert max_gap > 30, f"Gap should be > 30 days, got {max_gap}"
        
        filtered = filter_stations({"STN001": df}, max_gap_threshold=30, missing_ratio_threshold=0.15)
        assert "STN001" not in filtered, "Station with large gap should be excluded."

    def test_multiple_gaps_keeping_largest(self):
        """Station with multiple gaps, largest is 35 days, should be excluded."""
        # 10 days, 35 day gap, 10 days, 20 day gap, 10 days
        dates1 = pd.date_range("2000-01-01", periods=10, freq="D")
        # Gap 1: 35 days
        dates2 = pd.date_range("2000-03-16", periods=10, freq="D") # Jan 11 + 35 days = Feb 15?
        # Jan 1-10 (10 days). Next is Jan 11.
        # Skip 35 days: Jan 11 to Feb 14 (35 days).
        # Next: Feb 15.
        # Let's calculate properly.
        # Start: 2000-01-01. 10 days -> 2000-01-10.
        # Next date after 35 day gap: 2000-01-11 + 35 days = 2000-02-15.
        
        dates1 = pd.date_range("2000-01-01", periods=10, freq="D")
        dates2 = pd.date_range("2000-02-15", periods=10, freq="D")
        
        # Gap 2: 20 days.
        # Last date of part 2: 2000-02-24.
        # Next date: 2000-02-25 + 20 days = 2000-03-16.
        dates3 = pd.date_range("2000-03-16", periods=10, freq="D")
        
        all_dates = dates1.append(dates2).append(dates3)
        values = np.ones(len(all_dates))
        
        df = self._create_station_df(all_dates, values)
        
        max_gap = find_max_contiguous_gap(df)
        assert max_gap == 35, f"Max gap should be 35 days, got {max_gap}"
        
        filtered = filter_stations({"STN001": df}, max_gap_threshold=30, missing_ratio_threshold=0.15)
        assert "STN001" not in filtered, "Station with 35 day gap should be excluded."

    def test_gap_with_missing_values(self):
        """Verify gap calculation handles NaN values correctly as missing."""
        # Create a continuous date range but with NaN values in the middle
        dates = pd.date_range("2000-01-01", periods=50, freq="D")
        values = np.ones(50)
        # Set a 35 day block to NaN
        values[10:45] = np.nan 
        
        df = self._create_station_df(dates, values)
        
        max_gap = find_max_contiguous_gap(df)
        # The gap is 35 days (indices 10 to 44 inclusive)
        assert max_gap == 35, f"Gap should be 35 days, got {max_gap}"
        
        filtered = filter_stations({"STN001": df}, max_gap_threshold=30, missing_ratio_threshold=0.15)
        assert "STN001" not in filtered, "Station with 35 day NaN gap should be excluded."

    def test_filter_stations_combines_missing_ratio_and_gap(self):
        """Verify that a station is excluded if it fails EITHER condition."""
        # Station A: Passes both
        dates_a = pd.date_range("2000-01-01", periods=365, freq="D")
        values_a = np.ones(365)
        df_a = self._create_station_df(dates_a, values_a, "STN_A")
        
        # Station B: Fails gap (>30 days)
        dates_b1 = pd.date_range("2000-01-01", periods=10, freq="D")
        dates_b2 = pd.date_range("2000-03-02", periods=10, freq="D")
        values_b = np.ones(20)
        df_b = self._create_station_df(dates_b1.append(dates_b2), values_b, "STN_B")
        
        # Station C: Fails missing ratio (>15%)
        dates_c = pd.date_range("2000-01-01", periods=100, freq="D")
        values_c = np.ones(100)
        values_c[85:] = np.nan # 15% missing
        df_c = self._create_station_df(dates_c, values_c, "STN_C")
        
        data = {"STN_A": df_a, "STN_B": df_b, "STN_C": df_c}
        
        filtered = filter_stations(data, max_gap_threshold=30, missing_ratio_threshold=0.15)
        
        assert "STN_A" in filtered, "STN_A should be kept."
        assert "STN_B" not in filtered, "STN_B should be excluded due to gap."
        assert "STN_C" not in filtered, "STN_C should be excluded due to missing ratio."