"""
Tests for code/data/align_data.py
"""
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.align_data import flag_gaps, merge_datasets

def test_flag_gaps_no_gaps():
    """Test that no gaps are flagged when dates are consecutive."""
    dates = pd.date_range(start='2020-01-01', periods=10, freq='D')
    df = pd.DataFrame({'date': dates, 'value': range(10)})
    result = flag_gaps(df, gap_threshold_days=30)
    
    assert result['is_data_gap'].sum() == 0
    assert all(~result['is_data_gap'])

def test_flag_gaps_large_gap():
    """Test that gaps > 30 days are flagged."""
    dates = [
        datetime(2020, 1, 1),
        datetime(2020, 1, 2),
        datetime(2020, 3, 1), # Gap of ~58 days
        datetime(2020, 3, 2)
    ]
    df = pd.DataFrame({'date': dates, 'value': range(4)})
    result = flag_gaps(df, gap_threshold_days=30)
    
    # First row is not a gap (no previous)
    # Row 2 (Jan 2) diff is 1 day -> False
    # Row 3 (Mar 1) diff is 58 days -> True
    # Row 4 (Mar 2) diff is 1 day -> False
    
    expected_gaps = [False, False, True, False]
    assert result['is_data_gap'].tolist() == expected_gaps

def test_merge_datasets_basic():
    """Test basic merging of flux and solar data."""
    # Flux data: long format
    flux_data = {
        'date': ['2020-01-01', '2020-01-01', '2020-01-02', '2020-01-02'],
        'rigidity': [1.0, 1.0, 1.0, 1.0],
        'species': ['proton', 'helium', 'proton', 'helium'],
        'flux': [100.0, 20.0, 102.0, 21.0]
    }
    flux_df = pd.DataFrame(flux_data)
    
    # Solar data
    solar_data = {
        'date': ['2020-01-01', '2020-01-02'],
        'sunspot_number': [50, 55]
    }
    solar_df = pd.DataFrame(solar_data)
    
    merged = merge_datasets(flux_df, solar_df)
    
    assert len(merged) == 2
    assert 'proton_flux' in merged.columns
    assert 'helium_flux' in merged.columns
    assert 'sunspot_number' in merged.columns
    
    # Check values for first row
    row0 = merged[merged['date'] == '2020-01-01'].iloc[0]
    assert row0['proton_flux'] == 100.0
    assert row0['helium_flux'] == 20.0
    assert row0['sunspot_number'] == 50

def test_merge_datasets_missing_solar():
    """Test merging when solar data is missing for a date."""
    flux_data = {
        'date': ['2020-01-01', '2020-01-02'],
        'rigidity': [1.0, 1.0],
        'species': ['proton', 'proton'],
        'flux': [100.0, 102.0]
    }
    flux_df = pd.DataFrame(flux_data)
    
    solar_data = {
        'date': ['2020-01-01'],
        'sunspot_number': [50]
    }
    solar_df = pd.DataFrame(solar_data)
    
    merged = merge_datasets(flux_df, solar_df)
    
    assert len(merged) == 2
    # 2020-01-02 should have NaN sunspot
    row1 = merged[merged['date'] == '2020-01-02'].iloc[0]
    assert pd.isna(row1['sunspot_number'])

def test_merge_datasets_unknown_species():
    """Test that unknown species are ignored or handled gracefully."""
    flux_data = {
        'date': ['2020-01-01', '2020-01-01', '2020-01-01'],
        'rigidity': [1.0, 1.0, 1.0],
        'species': ['proton', 'unknown_species', 'helium'],
        'flux': [100.0, 999.0, 20.0]
    }
    flux_df = pd.DataFrame(flux_data)
    
    solar_data = {
        'date': ['2020-01-01'],
        'sunspot_number': [50]
    }
    solar_df = pd.DataFrame(solar_data)
    
    merged = merge_datasets(flux_df, solar_df)
    
    # Should only have proton and helium columns
    assert 'proton_flux' in merged.columns
    assert 'helium_flux' in merged.columns
    # The unknown species should not create a column or should be dropped
    # Based on implementation, it is dropped before pivot
    assert len(merged) == 1
    assert merged['proton_flux'].iloc[0] == 100.0
    assert merged['helium_flux'].iloc[0] == 20.0