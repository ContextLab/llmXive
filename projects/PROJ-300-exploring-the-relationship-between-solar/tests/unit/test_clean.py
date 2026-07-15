"""
Unit tests for code/data/clean.py
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
import os
# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.clean import clean_and_resample


def test_clean_removes_nan():
    """Test that clean_and_resample removes rows with NaN values."""
    # Create OMNI data with a NaN
    dates_omni = pd.date_range(start='2023-01-01', periods=10, freq='1T')
    df_omni = pd.DataFrame({
        'timestamp': dates_omni,
        'Vsw': [400.0] * 5 + [np.nan] + [400.0] * 4,
        'Bz': [5.0] * 10
    })

    # Create THEMIS data without NaN
    dates_themis = pd.date_range(start='2023-01-01', periods=10, freq='1T')
    df_themis = pd.DataFrame({
        'timestamp': dates_themis,
        'Ey': [1.0] * 10
    })

    df_omni_clean, df_themis_clean = clean_and_resample(df_omni, df_themis)

    # Check that no NaN values remain in the resulting DataFrames
    assert not df_omni_clean.isna().any().any()
    assert not df_themis_clean.isna().any().any()


def test_clean_resamples_to_5min():
    """Test that clean_and_resample resamples to 5-minute intervals."""
    # Create high-frequency data (1 minute)
    dates_omni = pd.date_range(start='2023-01-01', periods=60, freq='1T')
    df_omni = pd.DataFrame({
        'timestamp': dates_omni,
        'Vsw': [400.0] * 60,
        'Bz': [5.0] * 60
    })

    dates_themis = pd.date_range(start='2023-01-01', periods=60, freq='1T')
    df_themis = pd.DataFrame({
        'timestamp': dates_themis,
        'Ey': [1.0] * 60
    })

    df_omni_clean, df_themis_clean = clean_and_resample(df_omni, df_themis)

    # 60 minutes / 5 minutes = 12 points expected
    # (Assuming perfect alignment and no boundary issues)
    assert len(df_omni_clean) == 12
    assert len(df_themis_clean) == 12

    # Check frequency of index
    assert df_omni_clean.index.freq == pd.Timedelta(minutes=5)


def test_clean_handles_empty_input():
    """Test that clean_and_resample handles empty DataFrames gracefully."""
    df_omni_empty = pd.DataFrame(columns=['timestamp', 'Vsw', 'Bz'])
    df_themis_empty = pd.DataFrame(columns=['timestamp', 'Ey'])

    df_omni_clean, df_themis_clean = clean_and_resample(df_omni_empty, df_themis_empty)

    assert df_omni_clean.empty
    assert df_themis_clean.empty


def test_clean_all_nan():
    """Test handling of a DataFrame that becomes all NaN after dropping."""
    dates_omni = pd.date_range(start='2023-01-01', periods=5, freq='1T')
    df_omni = pd.DataFrame({
        'timestamp': dates_omni,
        'Vsw': [np.nan] * 5,
        'Bz': [np.nan] * 5
    })

    dates_themis = pd.date_range(start='2023-01-01', periods=5, freq='1T')
    df_themis = pd.DataFrame({
        'timestamp': dates_themis,
        'Ey': [1.0] * 5
    })

    df_omni_clean, df_themis_clean = clean_and_resample(df_omni, df_themis)

    # OMNI should be empty after dropping all-NaN rows
    assert df_omni_clean.empty
    # THEMIS might be empty too if no overlap or if it drops due to reindexing
    # but at least it shouldn't crash
    assert isinstance(df_themis_clean, pd.DataFrame)


def test_clean_single_value():
    """Test handling of a single valid value."""
    dates_omni = pd.date_range(start='2023-01-01', periods=1, freq='1T')
    df_omni = pd.DataFrame({
        'timestamp': dates_omni,
        'Vsw': [400.0],
        'Bz': [5.0]
    })

    dates_themis = pd.date_range(start='2023-01-01', periods=1, freq='1T')
    df_themis = pd.DataFrame({
        'timestamp': dates_themis,
        'Ey': [1.0]
    })

    df_omni_clean, df_themis_clean = clean_and_resample(df_omni, df_themis)

    # Single point might be resampled into existence or dropped if freq doesn't match
    # The key is it doesn't crash and returns DataFrames
    assert isinstance(df_omni_clean, pd.DataFrame)
    assert isinstance(df_themis_clean, pd.DataFrame)
    # If they align, we might have 1 point
    if not df_omni_clean.empty:
        assert len(df_omni_clean) == 1
        assert len(df_themis_clean) == 1