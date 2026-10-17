"""
Unit tests for the ACE and NOAA fetchers.

These tests verify that:
1. The public signatures of `fetch_ace` and `fetch_noaa` match the specification.
2. The functions return a string path that points inside the `data/raw` directory.
3. The returned CSV files contain the required column headers.
"""

import os
import pytest
from datetime import datetime

from code.data.fetch import fetch_ace, fetch_noaa
from code.config import RAW_DATA_DIR, ACE_VARS, NOAA_VARS

@pytest.fixture(scope="module")
def sample_dates():
    # Use a short, recent interval that is guaranteed to exist in the NOAA live feeds
    # and is also available in the ACE yearly archives (e.g., the first week of 2020).
    return ("2020-01-01", "2020-01-07")

def test_fetch_ace_signature():
    assert callable(fetch_ace)
    assert fetch_ace.__code__.co_argcount == 2

def test_fetch_noaa_signature():
    assert callable(fetch_noaa)
    assert fetch_noaa.__code__.co_argcount == 2

def test_fetch_ace_output_path(sample_dates):
    start, end = sample_dates
    path = fetch_ace(start, end)
    # Path must be a string and point inside the raw data directory
    assert isinstance(path, str)
    assert os.path.commonpath([path, RAW_DATA_DIR]) == RAW_DATA_DIR
    # File must exist after the fetch
    assert os.path.isfile(path)

    # Verify required ACE columns are present
    import pandas as pd
    df = pd.read_csv(path)
    for col in ACE_VARS:
        assert col in df.columns, f"Missing ACE column {col}"
    assert "timestamp" in df.columns

def test_fetch_noaa_output_path(sample_dates):
    start, end = sample_dates
    path = fetch_noaa(start, end)
    assert isinstance(path, str)
    assert os.path.commonpath([path, RAW_DATA_DIR]) == RAW_DATA_DIR
    assert os.path.isfile(path)

    import pandas as pd
    df = pd.read_csv(path)
    for col in NOAA_VARS:
        assert col in df.columns, f"Missing NOAA column {col}"
    assert "timestamp" in df.columns