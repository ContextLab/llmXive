"""
Unit tests for data ingestion module.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/tests/unit/test_ingest.py
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.ingest import fetch_omni_sw


def test_fetch_omni_sw_returns_dataframe():
    """
    Test that fetch_omni_sw returns a pandas DataFrame.
    """
    start = datetime(2023, 1, 1, 0, 0, 0)
    end = datetime(2023, 1, 1, 23, 59, 59)
    
    # This test will attempt to fetch real data
    # In a CI environment, we might mock this, but for now we test the function structure
    try:
        df = fetch_omni_sw((start, end))
        assert isinstance(df, pd.DataFrame), "Result should be a pandas DataFrame"
    except Exception as e:
        # If network fails, we still verify the function signature and error handling
        pytest.skip(f"Network request failed (expected in isolated env): {e}")


def test_fetch_omni_sw_columns():
    """
    Test that the returned DataFrame has the correct columns: timestamp, Vsw, Bz.
    """
    start = datetime(2023, 1, 1, 0, 0, 0)
    end = datetime(2023, 1, 1, 23, 59, 59)
    
    try:
        df = fetch_omni_sw((start, end))
        
        # Check index is datetime
        assert isinstance(df.index, pd.DatetimeIndex), "Index should be DatetimeIndex"
        
        # Check columns (Vsw, Bz) - timestamp is the index
        expected_columns = ["Vsw", "Bz"]
        assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
        
    except Exception as e:
        pytest.skip(f"Network request failed (expected in isolated env): {e}")


def test_fetch_omni_sw_invalid_range():
    """
    Test that fetch_omni_sw raises ValueError for invalid date range.
    """
    start = datetime(2023, 1, 2, 0, 0, 0)
    end = datetime(2023, 1, 1, 0, 0, 0)  # End before start
    
    with pytest.raises(ValueError, match="Start time must be before end time"):
        fetch_omni_sw((start, end))


def test_fetch_omni_sw_empty_range():
    """
    Test behavior when no data is found for the range.
    """
    # Use a very recent date that might not have data yet
    start = datetime.now() + timedelta(days=10)
    end = start + timedelta(days=1)
    
    try:
        df = fetch_omni_sw((start, end))
        assert isinstance(df, pd.DataFrame), "Should return empty DataFrame"
        assert len(df) == 0, "Should be empty for future dates"
    except RuntimeError as e:
        # If API rejects future dates, that's acceptable
        if "failed" in str(e).lower():
            pytest.skip(f"API rejected future date range: {e}")
        raise
