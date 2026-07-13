"""
Integration tests for data filtering logic (MMSE/MOCA non-null check).
"""
import pytest
import pandas as pd
from pathlib import Path
from utils.io import load_csv, save_csv
from code.utils.stats import check_collinearity # Just to ensure imports work

def test_filter_eligible_subjects_logic():
    """
    Test the logic of filtering subjects based on MMSE/MOCA scores.
    This simulates the logic in 01_download_and_filter.py without running the full download.
    """
    # Create a mock dataframe similar to what parse_bids_metadata would produce
    data = {
        'subject_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04'],
        'mmse_t1': [28.0, 25.0, None, 29.0],
        'moca_t1': [27.0, None, 26.0, 28.0],
        'mmse_t2': [27.0, 24.0, 28.0, None],
        'moca_t2': [26.0, 25.0, None, 27.0]
    }
    df = pd.DataFrame(data)

    # Logic: Keep if (mmse_t1 or moca_t1) is not null AND (mmse_t2 or moca_t2) is not null
    def is_eligible(row):
        has_t1 = pd.notna(row['mmse_t1']) or pd.notna(row['moca_t1'])
        has_t2 = pd.notna(row['mmse_t2']) or pd.notna(row['moca_t2'])
        return has_t1 and has_t2

    eligible = df[df.apply(is_eligible, axis=1)]
    
    # Expected: sub-01 (has both), sub-02 (has both), sub-04 (has t1, t2 missing? No, t2 has mmse null, moca present -> has_t2 is True)
    # sub-01: t1(28,27), t2(27,26) -> OK
    # sub-02: t1(25,NA), t2(24,25) -> OK (has t1 via mmse, has t2 via both)
    # sub-03: t1(NA,26), t2(28,NA) -> OK (has t1 via moca, has t2 via mmse)
    # sub-04: t1(29,28), t2(NA,27) -> OK (has t1, has t2 via moca)
    # Wait, let's re-read the requirement: "filter for subjects with non‑null MMSE/MOCA at both timepoints"
    # This usually means: (MMSE or MOCA) at T1 AND (MMSE or MOCA) at T2.
    
    # Let's adjust the mock data to create a clear failure case
    data_fail = {
        'subject_id': ['sub-05'],
        'mmse_t1': [None],
        'moca_t1': [None],
        'mmse_t2': [28.0],
        'moca_t2': [27.0]
    }
    df_fail = pd.DataFrame(data_fail)
    assert not is_eligible(df_fail.iloc[0])

    assert len(eligible) == 4
    assert 'sub-01' in eligible['subject_id'].values
    assert 'sub-02' in eligible['subject_id'].values
    assert 'sub-03' in eligible['subject_id'].values
    assert 'sub-04' in eligible['subject_id'].values

def test_collinearity_filter_logic():
    """Test that collinearity filter correctly identifies high correlation."""
    from utils.stats import check_collinearity
    import numpy as np

    # Create data with high correlation (>0.95)
    x = np.random.rand(100)
    y = x * 1.0 + 0.01 # Almost identical
    
    corr, p = check_collinearity(x, y)
    assert corr > 0.95
