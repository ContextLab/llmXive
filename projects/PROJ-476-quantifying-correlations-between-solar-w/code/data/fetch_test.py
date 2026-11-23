"""
Test module for fetch.py functionality.
"""
import pytest
import os
from datetime import datetime
from code.data.fetch import fetch_ace, fetch_noaa
from code.config import ACE_VARS, NOAA_VARS


def test_fetch_ace_signature():
    """Test that fetch_ace has the correct signature."""
    # Just verify the function exists and has the right parameters
    import inspect
    sig = inspect.signature(fetch_ace)
    params = list(sig.parameters.keys())
    assert 'start_date' in params
    assert 'end_date' in params


def test_fetch_noaa_signature():
    """Test that fetch_noaa has the correct signature."""
    import inspect
    sig = inspect.signature(fetch_noaa)
    params = list(sig.parameters.keys())
    assert 'start_date' in params
    assert 'end_date' in params


def test_fetch_ace_output_path():
    """Test that fetch_ace returns the correct output path."""
    # This test will fail if the data source is unreachable, which is expected
    # We're just verifying the function structure
    try:
        result = fetch_ace("2020-01-01", "2020-01-02")
        assert result == "data/raw/ace_raw.csv"
    except ConnectionError:
        # Expected if the real data source is unreachable
        pytest.skip("Real data source unreachable")


def test_fetch_noaa_output_path():
    """Test that fetch_noaa returns the correct output path."""
    try:
        result = fetch_noaa("2020-01-01", "2020-01-02")
        assert result == "data/raw/noaa_raw.csv"
    except ConnectionError:
        pytest.skip("Real data source unreachable")